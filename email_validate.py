import os
import re
import dns.resolver
import smtplib
import socket
from typing import Dict, Optional, Tuple
from datetime import datetime
from validate_email import validate_email
from disposable_email_domains import allowlist, blocklist
from ultra_logger import Logger
from piapy import PiaVpn

class EmailValidator:
    """A comprehensive email validation class with enhanced features."""

    def __init__(self, logger: Optional[Logger] = None):
        """Initialize the EmailValidator with configuration and setup.

        Args:
            logger: Optional logger instance for custom logging
        """
        self.logger = logger or Logger('EmailValidator', 'logs/email_validator.log', log_to_console=True)
        self.setup_directories()
        self.vpn = PiaVpn()
        
        # SMTP connection settings
        self.mailer = {
            'timeout': 10,  # seconds
            'retry_count': 3,
            'retry_delay': 2,  # seconds
            'ports': [25, 587, 465],
            'helo_host': 'gmail.com'
        }

        # Cache for validation results
        self.domain_cache = {
            'mx_records': {},
            'disposable': set(blocklist) - set(allowlist),  # Using blocklist and allowlist for better accuracy
            'catchall': {},
            'deliverable': {}
        }

    def setup_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = ['logs', 'data']
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                self.logger.info(f'Created directory: {directory}')

        # Initialize data files if they don't exist
        data_files = [
            'valid_domains.txt',
            'catchall_domains.txt',
            'not_catchall_domains.txt',
            'verified_emails.txt'
        ]
        for filename in data_files:
            file_path = os.path.join('data', filename)
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    pass
                self.logger.info(f'Created file: {filename}')

    def validate(self, email: str) -> Dict[str, any]:
        """Validate an email address comprehensively.

        Args:
            email: The email address to validate

        Returns:
            Dictionary containing validation results
        """
        start_time = datetime.now()
        result = {
            'email': email,
            'is_valid': False,
            'has_mx_record': False,
            'is_disposable': False,
            'is_catchall': False,
            'is_deliverable': False,
            'quality_score': 0.0,
            'validation_time': None,
            'error': None
        }

        try:
            # Basic syntax validation
            result['is_valid'] = bool(validate_email(email, check_format=True, check_blacklist=False, check_dns=False))
            if not result['is_valid']:
                return self._finalize_result(result, start_time)

            # Extract domain
            _, domain = email.split('@')

            # Check MX records
            result['has_mx_record'] = self._check_mx_record(domain)
            if not result['has_mx_record']:
                return self._finalize_result(result, start_time)

            # Check if disposable
            result['is_disposable'] = domain not in self.domain_cache['disposable']  # Inverted logic since we're using allowlist
            if result['is_disposable']:
                return self._finalize_result(result, start_time)

            # Check catchall status
            result['is_catchall'] = self._check_catchall(domain)

            # Check deliverability
            result['is_deliverable'] = self._check_deliverability(email, domain)

            # Calculate quality score
            result['quality_score'] = self._calculate_quality_score(result)

        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f'Error validating {email}: {str(e)}')

        return self._finalize_result(result, start_time)

    def _check_mx_record(self, domain: str) -> bool:
        """Check if domain has valid MX records."""
        if domain in self.domain_cache['mx_records']:
            return self.domain_cache['mx_records'][domain]

        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            has_mx = bool(mx_records)
            self.domain_cache['mx_records'][domain] = has_mx
            return has_mx
        except Exception as e:
            self.logger.debug(f'MX record check failed for {domain}: {str(e)}')
            return False

    def _check_catchall(self, domain: str) -> bool:
        """Check if domain has catchall configuration."""
        if domain in self.domain_cache['catchall']:
            return self.domain_cache['catchall'][domain]

        test_email = f'test_nonexistent_email_{datetime.now().timestamp()}@{domain}'
        is_catchall = self._check_deliverability(test_email, domain)
        self.domain_cache['catchall'][domain] = is_catchall
        return is_catchall

    def _check_deliverability(self, email: str, domain: str) -> bool:
        """Check if email address is deliverable."""
        if email in self.domain_cache['deliverable']:
            return self.domain_cache['deliverable'][email]

        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_hosts = [str(mx.exchange).rstrip('.') for mx in mx_records]

            for mx_host in mx_hosts:
                for port in self.mailer['ports']:
                    try:
                        with smtplib.SMTP(mx_host, port, timeout=self.mailer['timeout']) as smtp:
                            smtp.ehlo(self.mailer['helo_host'])
                            if port == 587:
                                smtp.starttls()
                                smtp.ehlo(self.mailer['helo_host'])
                            code, message = smtp.verify(email)
                            is_deliverable = code == 250 or code == 251 or code == 252
                            self.domain_cache['deliverable'][email] = is_deliverable
                            return is_deliverable
                    except (socket.timeout, smtplib.SMTPServerDisconnected):
                        continue
                    except Exception as e:
                        self.logger.debug(f'SMTP verification failed for {email} on {mx_host}:{port}: {str(e)}')
                        continue

        except Exception as e:
            self.logger.error(f'Deliverability check failed for {email}: {str(e)}')

        return False

    def _calculate_quality_score(self, result: Dict[str, any]) -> float:
        """Calculate email quality score based on validation results."""
        score = 0.0
        weights = {
            'is_valid': 0.2,
            'has_mx_record': 0.2,
            'not_disposable': 0.2,
            'not_catchall': 0.2,
            'is_deliverable': 0.2
        }

        if result['is_valid']:
            score += weights['is_valid']
        if result['has_mx_record']:
            score += weights['has_mx_record']
        if not result['is_disposable']:
            score += weights['not_disposable']
        if not result['is_catchall']:
            score += weights['not_catchall']
        if result['is_deliverable']:
            score += weights['is_deliverable']

        return round(score, 2)

    def _finalize_result(self, result: Dict[str, any], start_time: datetime) -> Dict[str, any]:
        """Finalize validation result with timing information."""
        result['validation_time'] = (datetime.now() - start_time).total_seconds()
        return result

    def clear_cache(self) -> None:
        """Clear validation result caches."""
        self.domain_cache = {
            'mx_records': {},
            'disposable': set(allowlist),  # Using allowlist instead of domains
            'catchall': {},
            'deliverable': {}
        }
        self.logger.info('Cache cleared')
    