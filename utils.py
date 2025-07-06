from typing import Dict, List, Optional, Set, Tuple, Union
import csv
import os
from datetime import datetime
from ultra_logger import Logger

class EmailUtils:
    """Utility class for email validation and file operations."""

    @staticmethod
    def parse_log(log_file: str, logger: Optional[Logger] = None) -> List[Dict[str, str]]:
        """Parse log file to extract RCPT TO command results.

        Args:
            log_file: Path to the log file
            logger: Optional logger instance

        Returns:
            List of dictionaries containing email and status information
        """
        logger = logger or Logger('Utils_logs', 'logs/utils_logs.log', log_to_console=True)
        results = []

        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()

            current_email = None
            for line in lines:
                if 'RCPT TO command result:' in line:
                    parts = line.split('RCPT TO command result:')
                    if len(parts) == 2:
                        status_parts = parts[1].strip().split(',', 1)
                        if len(status_parts) == 2:
                            code = status_parts[0].strip()
                            message = status_parts[1].strip()
                            if current_email:
                                results.append({
                                    'email': current_email,
                                    'status_code': code,
                                    'status_message': message,
                                    'timestamp': datetime.now().isoformat()
                                })
                elif 'Checking deliverability for' in line:
                    current_email = line.split('Checking deliverability for')[-1].strip()

            return results

        except Exception as e:
            logger.error(f'Error parsing log file: {str(e)}')
            return []

    @staticmethod
    def update_files(csv_file: str, logger: Optional[Logger] = None) -> None:
        """Update domain and email lists based on validation results.

        Args:
            csv_file: Path to the CSV file containing validation results
            logger: Optional logger instance
        """
        logger = logger or Logger('Utils_logs', 'logs/utils_logs.log', log_to_console=True)

        try:
            # Initialize sets for different types of domains and emails
            valid_domains: Set[str] = set()
            catchall_domains: Set[str] = set()
            not_catchall_domains: Set[str] = set()
            verified_emails: Set[str] = set()

            # Read existing data from files
            data_files = {
                'valid_domains.txt': valid_domains,
                'catchall_domains.txt': catchall_domains,
                'not_catchall_domains.txt': not_catchall_domains,
                'verified_emails.txt': verified_emails
            }

            for filename, data_set in data_files.items():
                file_path = os.path.join('data', filename)
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        data_set.update(line.strip() for line in f)

            # Process CSV file
            with open(csv_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    email = row['email']
                    domain = email.split('@')[1]

                    # Update domain sets based on validation results
                    if row.get('has_mx_record') == 'True':
                        valid_domains.add(domain)

                    if row.get('is_catchall') == 'True':
                        catchall_domains.add(domain)
                    elif row.get('is_catchall') == 'False':
                        not_catchall_domains.add(domain)

                    if row.get('is_deliverable') == 'True':
                        verified_emails.add(email)

            # Write updated data back to files
            for filename, data_set in data_files.items():
                file_path = os.path.join('data', filename)
                with open(file_path, 'w') as f:
                    for item in sorted(data_set):
                        f.write(f'{item}\n')

            logger.info('Successfully updated domain and email lists')

        except Exception as e:
            logger.error(f'Error updating files: {str(e)}')
            raise

    @staticmethod
    def clean_email_list(input_file: str, output_file: str, logger: Optional[Logger] = None) -> None:
        """Clean and deduplicate email list.

        Args:
            input_file: Path to the input file containing emails
            output_file: Path to write cleaned emails
            logger: Optional logger instance
        """
        logger = logger or Logger('Utils_logs', 'logs/utils_logs.log', log_to_console=True)

        try:
            # Read and clean emails
            cleaned_emails = set()
            with open(input_file, 'r') as f:
                for line in f:
                    email = line.strip().lower()
                    if email and '@' in email:
                        cleaned_emails.add(email)

            # Write cleaned emails
            with open(output_file, 'w') as f:
                for email in sorted(cleaned_emails):
                    f.write(f'{email}\n')

            logger.info(f'Cleaned {len(cleaned_emails)} unique emails')

        except Exception as e:
            logger.error(f'Error cleaning email list: {str(e)}')
            raise

    @staticmethod
    def analyze_results(csv_file: str, logger: Optional[Logger] = None) -> Dict[str, Union[int, float]]:
        """Analyze validation results and generate statistics.

        Args:
            csv_file: Path to the CSV file containing validation results
            logger: Optional logger instance

        Returns:
            Dictionary containing validation statistics
        """
        logger = logger or Logger('Utils_logs', 'logs/utils_logs.log', log_to_console=True)

        try:
            stats = {
                'total_emails': 0,
                'valid_syntax': 0,
                'has_mx_record': 0,
                'not_disposable': 0,
                'not_catchall': 0,
                'deliverable': 0,
                'avg_quality_score': 0.0
            }

            with open(csv_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    stats['total_emails'] += 1
                    if row.get('is_valid') == 'True':
                        stats['valid_syntax'] += 1
                    if row.get('has_mx_record') == 'True':
                        stats['has_mx_record'] += 1
                    if row.get('is_disposable') == 'False':
                        stats['not_disposable'] += 1
                    if row.get('is_catchall') == 'False':
                        stats['not_catchall'] += 1
                    if row.get('is_deliverable') == 'True':
                        stats['deliverable'] += 1
                    if row.get('quality_score'):
                        stats['avg_quality_score'] += float(row['quality_score'])

            if stats['total_emails'] > 0:
                stats['avg_quality_score'] /= stats['total_emails']

            logger.info('Successfully analyzed validation results')
            return stats

        except Exception as e:
            logger.error(f'Error analyzing results: {str(e)}')
            return stats