import os
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Set, Dict, Optional
from datetime import datetime
from tqdm import tqdm
from email_validate import EmailValidator
from utils import EmailUtils
from ultra_logger import Logger

class BulkEmailVerifier:
    """A class for bulk email verification with enhanced features."""

    def __init__(self, input_file: str = 'emails.txt', output_file: str = 'emails_validated.csv',
                 max_workers: int = 5, logger: Optional[Logger] = None):
        """Initialize the bulk email verifier.

        Args:
            input_file: Path to the input file containing email addresses
            output_file: Path to the output CSV file for validation results
            max_workers: Maximum number of concurrent validation workers
            logger: Optional logger instance
        """
        self.input_file = input_file
        self.output_file = output_file
        self.max_workers = max_workers
        self.logger = logger or Logger('BulkVerifier', 'logs/bulk_verifier.log', log_to_console=True)
        self.validator = EmailValidator(self.logger)
        self.utils = EmailUtils()
        self.existing_emails = self._load_existing_emails()

    def _load_existing_emails(self) -> Set[str]:
        """Load previously validated emails from the output file."""
        existing_emails = set()
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', newline='') as f:
                    reader = csv.DictReader(f)
                    existing_emails = {row['email'] for row in reader}
            except Exception as e:
                self.logger.error(f'Error loading existing emails: {str(e)}')
        return existing_emails

    def _read_input_emails(self) -> List[str]:
        """Read and deduplicate input emails."""
        try:
            with open(self.input_file, 'r') as f:
                emails = {line.strip().lower() for line in f if line.strip() and '@' in line}
            return list(emails - self.existing_emails)
        except Exception as e:
            self.logger.error(f'Error reading input emails: {str(e)}')
            return []

    def _ensure_output_file(self) -> None:
        """Ensure the output CSV file exists with correct headers."""
        headers = [
            'email', 'is_valid', 'has_mx_record', 'is_disposable', 'is_catchall',
            'is_deliverable', 'quality_score', 'validation_time', 'error',
            'validation_date'
        ]

        try:
            # Create output directory if it doesn't exist
            output_dir = os.path.dirname(self.output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Create file with headers if it doesn't exist
            if not os.path.exists(self.output_file):
                with open(self.output_file, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                # Set initial permissions
                os.chmod(self.output_file, 0o666)
            else:
                # Ensure existing file is writable
                os.chmod(self.output_file, 0o666)
        except PermissionError as pe:
            self.logger.error(f'Permission denied when creating/modifying {self.output_file}. Please check directory permissions.')
            raise
        except Exception as e:
            self.logger.error(f'Error ensuring output file: {str(e)}')
            raise

    def _validate_email(self, email: str) -> Dict[str, any]:
        """Validate a single email with retry logic."""
        try:
            result = self.validator.validate(email)
            result['validation_date'] = datetime.now().isoformat()
            return result
        except Exception as e:
            self.logger.error(f'Error validating {email}: {str(e)}')
            return {
                'email': email,
                'is_valid': False,
                'has_mx_record': False,
                'is_disposable': False,
                'is_catchall': False,
                'is_deliverable': False,
                'quality_score': 0.0,
                'validation_time': None,
                'error': str(e),
                'validation_date': datetime.now().isoformat()
            }

    def _write_results(self, results: List[Dict[str, any]]) -> None:
        """Write validation results to the output file with proper error handling."""
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(self.output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Set proper file permissions
            if os.path.exists(self.output_file):
                os.chmod(self.output_file, 0o666)

            # Write results with exclusive access
            with open(self.output_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writerows(results)

            # Reset permissions to read-only after writing
            os.chmod(self.output_file, 0o444)
        except PermissionError as pe:
            self.logger.error(f'Permission denied when writing to {self.output_file}. Please check file permissions.')
            raise
        except Exception as e:
            self.logger.error(f'Error writing results: {str(e)}')
            raise

    def validate_emails(self) -> None:
        """Validate emails in bulk with progress tracking."""
        try:
            self._ensure_output_file()
            emails = self._read_input_emails()

            if not emails:
                self.logger.info('No new emails to validate')
                return

            self.logger.info(f'Starting validation of {len(emails)} emails')
            results = []
            batch_size = 100

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self._validate_email, email): email for email in emails}
                
                with tqdm(total=len(emails), desc='Validating emails') as pbar:
                    for future in as_completed(futures):
                        result = future.result()
                        results.append(result)
                        pbar.update(1)

                        # Write results in batches
                        if len(results) >= batch_size:
                            self._write_results(results)
                            results = []

            # Write remaining results
            if results:
                self._write_results(results)

            # Update domain and email lists
            self.utils.update_files(self.output_file)
            self.validator.clear_cache()

            # Generate and log statistics
            stats = self.utils.analyze_results(self.output_file)
            self.logger.info('Validation completed. Statistics:')
            for key, value in stats.items():
                self.logger.info(f'{key}: {value}')

        except Exception as e:
            self.logger.error(f'Bulk validation failed: {str(e)}')
            raise

if __name__ == '__main__':
    verifier = BulkEmailVerifier()
    verifier.validate_emails()
          
          

    
    
    
