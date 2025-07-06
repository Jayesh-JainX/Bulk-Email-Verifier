# 📋 Email Validation Project

## 📝 Description

This project provides a robust email validation system that performs comprehensive checks on email addresses. It verifies syntax, MX records, disposable email domains, catchall status, and email deliverability. The system is designed for accuracy, reliability, and respect for email server policies.

## 🌟 Features

- **Syntax Validation**: Ensures email addresses follow RFC standards
- **MX Record Verification**: Checks domain's ability to receive emails
- **Disposable Email Detection**: Identifies temporary email providers
- **Catchall Status**: Verifies if domains accept all incoming emails
- **Deliverability Check**: Validates email existence without sending messages
- **Advanced Logging**: Detailed tracking of validation processes
- **VPN Integration**: Enhanced privacy and reliability with PIA VPN support
- **Batch Processing**: Efficient handling of multiple email validations
- **Result Caching**: Improves performance for repeated validations
- **Error Recovery**: Automatic retry mechanism for failed validations

## 💻 Requirements

- Python 3.10.4 or higher
- Windows/Linux/MacOS
- PIA VPN (Optional, for enhanced privacy)
- Stable internet connection
- Sufficient system memory (minimum 4GB RAM recommended)

## 🛠️ Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/Jayesh-JainX/Bulk-Email-Verifier.git
   cd Bulk-Email-Verifier
   ```

2. Create and activate virtual environment:

   ```bash
   # Create virtual environment
   python -m venv venv

   # Windows activation
   .\venv\Scripts\activate

   # Linux/MacOS activation
   source venv/bin/activate
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## 📁 Project Structure

```
email-verification/
├── bulk_verifier.py     # Main script for bulk email validation
├── email_validate.py    # Core validation logic and EmailValidator class
├── utils.py            # Utility functions and helper classes
├── logger.py           # Logging configuration
├── requirements.txt    # Project dependencies
├── .gitignore         # Git ignore rules
├── emails.txt         # Input file for email addresses
├── logs/              # Validation logs directory
└── data/              # Validation data directory
    ├── valid_domains.txt
    ├── catchall_domains.txt
    └── not_catchall_domains.txt
```

## 🚀 Usage

1. Prepare email list:

   - Create or modify `emails.txt` with one email per line
   - Supports both plain emails and CSV format
   - Automatically handles duplicates

2. Configure validation settings (optional):

   - Adjust retry attempts in `email_validate.py`
   - Modify timeout settings if needed
   - Configure VPN settings if using PIA

3. Run the validator:

   ```bash
   # Activate virtual environment first if not activated
   python bulk_verifier.py
   ```

4. Monitor progress:
   - Check terminal for real-time progress
   - Review logs in the `logs` directory
   - Results saved in `emails_validated.csv`

## 📊 Output Format

The validation results (`emails_validated.csv`) include:

| Column          | Description                           |
| --------------- | ------------------------------------- |
| email           | Email address                         |
| is_valid        | Syntax validation result              |
| is_catchall     | Domain accepts all emails             |
| is_deliverable  | Email exists and can receive mail     |
| is_disposable   | Temporary/disposable email service    |
| has_mx_records  | Valid MX records exist                |
| quality_score   | Overall validation confidence (0-100) |
| validation_time | Time taken for validation             |
| last_checked    | Timestamp of last verification        |

## ⚠️ Rate Limiting and Privacy

- **Rate Limiting**: Implements automatic delays between requests
- **VPN Support**: Integrated PIA VPN support for privacy
- **Server Respect**: Honors email server rate limits
- **Error Handling**: Automatic retry with exponential backoff
- **IP Rotation**: Optional VPN-based IP rotation

## 🎯 Accuracy Improvements

- Multiple SMTP ports testing (25, 587, 465)
- Advanced MX record verification
- Sophisticated catchall detection
- Comprehensive disposable email database
- Quality scoring system
- Connection pooling and timeout handling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add/update tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚡ Performance Tips

- Use VPN for large-scale validation
- Implement appropriate delays between checks
- Consider using batch processing for large lists
- Monitor system resources during validation
- Review logs regularly for optimization opportunities

## 🔧 Troubleshooting

- Ensure Python 3.10.4 or higher is installed
- Check virtual environment activation
- Verify all dependencies are installed
- Review logs for specific error messages
- Ensure proper network connectivity
- Check VPN configuration if using PIA
