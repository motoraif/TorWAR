# 🛡️ TorWAR - AWS Well-Architected Review Tool

> **Tor**aif's **W**ell-**A**rchitected **R**eview Tool - A streamlined, user-friendly web application for conducting comprehensive AWS Well-Architected Framework reviews with advanced report generation and management capabilities.

**Author:** Mohamed Toraif  
**Created:** 2024
**License:** MIT

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com)
[![AWS](https://img.shields.io/badge/AWS-Well--Architected-orange.svg)](https://aws.amazon.com/architecture/well-architected)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)](https://getbootstrap.com)

## 🌟 Features

### 🔐 **Authentication & Security**
- **AWS Profile Authentication**: Secure authentication using AWS CLI profiles
- **Session Management**: Persistent sessions with automatic timeout
- **Multi-Account Support**: Switch between different AWS accounts seamlessly

### 🏗️ **Workload Management**
- **Create Workloads**: Set up new Well-Architected workloads
- **Workload Selection**: Easy workload switching and management
- **Account Integration**: Direct integration with AWS Well-Architected Tool

### 📋 **Review Process**
- **Interactive Questionnaire**: User-friendly interface for framework questions
- **Pillar-based Reviews**: Comprehensive coverage of all 6 Well-Architected pillars:
  - 🏛️ Operational Excellence
  - 🔒 Security
  - 🛡️ Reliability
  - ⚡ Performance Efficiency
  - 💰 Cost Optimization
  - ♻️ Sustainability
- **Progress Tracking**: Real-time completion status and progress indicators
- **Risk Assessment**: Automatic risk level calculation and categorization

### 📊 **Report Generation & Management**
- **Professional Reports**: Clean, print-ready reports with comprehensive analysis
- **Multiple Formats**: Optimized for both web viewing and printing
- **Report Versioning**: Track changes and improvements over time
- **Report Comparison**: Side-by-side comparison of different report versions
- **Export Options**: Print-friendly layouts with professional styling

### 🎨 **User Experience**
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Intuitive Navigation**: Clean, organized interface with logical flow
- **Real-time Feedback**: Instant validation and progress updates
- **Accessibility**: WCAG-compliant design for inclusive access

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** installed on your system
- **AWS CLI** configured with valid credentials
- **AWS Account** with Well-Architected Tool access
- **Modern Web Browser** (Chrome, Firefox, Safari, Edge)

### Installation

#### Option 1: Docker (Recommended)

1. **Clone the repository:**
```bash
git clone https://github.com/your-username/TorWAR.git
cd TorWAR
```

2. **Configure AWS credentials:**
```bash
aws configure
```

3. **Build and start:**
```bash
./docker-manage.sh build
./docker-manage.sh start
```

4. **Access the application:**
   - Open your browser: `http://localhost:5000`

See [DOCKER.md](DOCKER.md) for detailed Docker documentation.

#### Option 2: Local Installation

1. **Clone the repository:**
```bash
git clone https://github.com/your-username/TorWAR.git
cd TorWAR
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure AWS credentials:**
```bash
# Option 1: Using AWS CLI
aws configure --profile torwar-profile

# Option 2: Using environment variables
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=us-east-1
```

4. **Set up environment (optional):**
```bash
cp .env.example .env
# Edit .env with your preferred settings
```

### Running the Application

#### Docker
```bash
./docker-manage.sh start    # Start
./docker-manage.sh logs     # View logs
./docker-manage.sh stop     # Stop
```

#### Local
1. **Start the server:**
```bash
python3 app.py
```

2. **Access the application:**
   - Open your browser and navigate to: `http://localhost:5000`
   - Or access via network: `http://your-ip:5000`

3. **Begin your review:**
   - Authenticate with your AWS profile
   - Create or select a workload
   - Start your Well-Architected review

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```bash
# Application Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
PORT=5000

# AWS Settings (optional - can use AWS CLI profiles instead)
AWS_DEFAULT_REGION=us-east-1
AWS_PROFILE=torwar-profile

# Application Behavior
AUTO_SAVE_INTERVAL=300  # Auto-save every 5 minutes
MAX_REPORTS_PER_WORKLOAD=10
```

### AWS Permissions

Your AWS user/role needs the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "wellarchitected:*"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "sts:GetCallerIdentity",
                "iam:ListAccountAliases"
            ],
            "Resource": "*"
        }
    ]
}
```

## 📁 Project Structure

```
TorWAF/
├── 📄 app.py                      # Main Flask application
├── 🔐 aws_auth.py                 # AWS authentication logic
├── 🛣️ aws_auth_routes.py          # Authentication routes
├── 🔧 aws_helper.py               # AWS session management
├── 📊 report_manager.py           # Report generation & management
├── 📋 requirements.txt            # Python dependencies
├── ⚙️ .env.example                # Environment configuration template
├── 🎨 templates/                  # HTML templates
│   ├── 🏠 index.html              # Homepage
│   ├── 📝 answer_question.html    # Question interface
│   ├── 📊 generate_report.html    # Report generation
│   ├── 💾 saved_reports.html      # Report management
│   ├── 🔍 compare_reports.html    # Report comparison
│   └── 🎯 base.html               # Base template
├── 🎨 static/                     # Static assets
│   └── 🖼️ logo.svg               # TorWAR logo
├── 💾 data/                       # Application data
│   ├── 📊 reports/                # Saved reports
│   │   ├── metadata/              # Report metadata
│   │   └── workloads/             # Workload data
│   └── 🏗️ workloads/             # Workload configurations
├── 🧪 testing/                    # Test files and documentation
└── 📝 logs/                       # Application logs
```

## 🎯 Usage Guide

### 1. **Initial Setup**
- Launch the application and navigate to the homepage
- Click "AWS Login" to authenticate with your AWS credentials
- Select your preferred AWS region and profile

### 2. **Workload Management**
- Create a new workload or select an existing one
- Provide workload details (name, description, environment)
- Configure workload-specific settings

### 3. **Conducting Reviews**
- Select pillars to review (or choose "All Pillars")
- Answer questions for each pillar systematically
- Use the help hints and best practices provided
- Save progress automatically or manually

### 4. **Report Generation**
- Generate comprehensive reports after completing reviews
- Customize report names and add notes
- View reports in clean, professional format
- Print or export reports as needed

### 5. **Report Management**
- Access all saved reports from the Reports menu
- Compare different versions of reports
- Track improvements and changes over time
- Delete outdated reports when needed

## 🔍 Key Features Explained

### **Simplified Report Viewing**
- Clean, chart-free interface for easy reading
- Color-coded risk indicators (Red=High, Yellow=Medium, Blue=Low, Green=None)
- Print-optimized layouts
- No auto-scrolling or animations

### **Report Comparison**
- Side-by-side comparison of any two reports
- Highlight changes and improvements
- Track risk reduction over time
- Identify areas needing attention

### **Responsive Design**
- Works on all device sizes
- Touch-friendly interface for tablets
- Keyboard navigation support
- High contrast mode available

## 🛠️ Development

### **Running in Development Mode**

```bash
# Enable debug mode
export FLASK_ENV=development
export DEBUG=True
python3 app.py
```

### **Testing**

```bash
# Run basic functionality tests
cd testing/
python3 -m pytest

# Manual testing endpoints
curl http://localhost:5000/health
curl http://localhost:5000/saved_reports
```

### **Contributing**

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -m 'Add amazing feature'`
5. Push to the branch: `git push origin feature/amazing-feature`
6. Open a Pull Request

## 🐛 Troubleshooting

### **Common Issues**

**Q: "Error loading saved reports" or template errors**
- **A:** All template issues have been resolved in the latest version. Ensure you're using the updated codebase.

**Q: AWS authentication fails**
- **A:** Check your AWS credentials and permissions. Ensure the Well-Architected service is available in your region.

**Q: Reports not saving**
- **A:** Verify write permissions to the `data/reports/` directory.

**Q: Page keeps scrolling or charts not loading**
- **A:** The UI has been simplified to remove problematic animations and charts.

### **Getting Help**

- 📧 **Issues**: Open an issue on GitHub
- 📖 **Documentation**: Check the `testing/` directory for detailed guides
- 🔧 **Configuration**: Review the `.env.example` file for all options

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **AWS Well-Architected Framework** for the comprehensive review methodology
- **Flask Community** for the excellent web framework
- **Bootstrap Team** for the responsive UI components
- **Contributors** who helped improve and test the application

## 🚀 What's Next?

- 📊 Enhanced analytics and trending
- 🔄 Automated report scheduling
- 👥 Multi-user collaboration features
- 📱 Mobile app companion
- 🔗 Integration with other AWS services

---

**Created by Mohamed Toraif with ❤️ in Bahrain 🇧🇭**

*TorWAR - Making AWS Well-Architected Reviews Simple and Effective*

**© 2024 Mohamed Toraif. Licensed under MIT License.**
