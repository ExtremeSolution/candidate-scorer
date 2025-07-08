# Contributing to HR Candidate Scorer

Thank you for your interest in contributing to the HR Candidate Scorer! This open-source project democratizes AI-powered candidate evaluation by providing an enterprise-grade, cost-effective alternative to expensive HR tools.

## 🎯 Project Mission

Transform hiring processes by making advanced AI candidate scoring accessible to organizations of all sizes, reducing costs from $200-500/month enterprise solutions to $25-65/month through open-source innovation.

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Google Cloud Platform account
- Git

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/hr-agent.git
   cd hr-agent
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Test locally**
   ```bash
   python test_local.py
   ```

## 📝 How to Contribute

### Reporting Issues

- Use GitHub Issues to report bugs or request features
- Use the appropriate issue template
- Include detailed information and steps to reproduce

### Submitting Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow existing code style
   - Add tests if applicable
   - Update documentation

3. **Test your changes**
   ```bash
   python test_local.py
   ./deploy.sh  # Test deployment
   ./cleanup.sh # Test cleanup
   ```

4. **Submit a pull request**
   - Use the pull request template
   - Include a clear description of changes
   - Reference any related issues

## 🎨 Code Style Guidelines

### Python Code
- Follow PEP 8 style guide
- Use meaningful variable and function names
- Add docstrings for functions and classes
- Keep functions focused and small

### Frontend Code
- Use consistent indentation (2 spaces)
- Follow semantic HTML structure
- Use CSS classes over inline styles
- Ensure mobile responsiveness

### Documentation
- Use clear, concise language
- Include code examples where helpful
- Update README.md for significant changes

## 🏗️ Architecture Guidelines

### Core Principles
- **Simplicity**: One-command deployment and cleanup
- **Reliability**: Robust error handling and fallbacks
- **Cost-Effectiveness**: Optimize for minimal GCP costs
- **Security**: Never commit credentials or sensitive data

### Key Components
- **main.py**: Core Flask application
- **analyze_company.py**: Company analysis and enhanced scoring
- **deploy.sh**: Automated deployment script
- **cleanup.sh**: Complete resource cleanup
- **templates/**: UI templates with modern styling

## 🧪 Testing

### Local Testing
```bash
python test_local.py
```

### Deployment Testing
```bash
./deploy.sh
# Test the deployed application
./cleanup.sh
```

### Manual Testing Checklist
- [ ] UI loads correctly
- [ ] Progress indicators work
- [ ] File upload functions
- [ ] Company analysis enhances scoring
- [ ] Results display properly
- [ ] Mobile responsiveness

## 🌟 Feature Development

### Priority Areas
1. **Enhanced Scoring Algorithms**: Improve AI analysis accuracy
2. **Additional Data Sources**: LinkedIn, GitHub integration
3. **Multi-language Support**: Internationalization
4. **Advanced Analytics**: Candidate comparison features
5. **Integration APIs**: Webhook support, ATS integration

### Feature Process
1. **Propose**: Create a feature request issue
2. **Discuss**: Community discussion and feedback
3. **Design**: Technical design document
4. **Implement**: Development with tests
5. **Review**: Code review and testing
6. **Deploy**: Merge and release

## 📋 Issue Labels

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Improvements or additions to docs
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed
- `priority:high`: Critical issues
- `priority:medium`: Important improvements
- `priority:low`: Nice-to-have features

## 🤝 Community Guidelines

### Be Respectful
- Use welcoming and inclusive language
- Respect differing viewpoints and experiences
- Accept constructive criticism gracefully

### Be Collaborative
- Help newcomers get started
- Share knowledge and best practices
- Credit others for their contributions

### Be Professional
- Focus on the technical merit of ideas
- Avoid personal attacks or harassment
- Keep discussions on-topic

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and community chat
- **Documentation**: Check README.md and code comments

## 🏆 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- Special thanks for major features

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

---

**Ready to contribute?** Check out our [good first issues](https://github.com/extremesolution/hr-agent/labels/good%20first%20issue) to get started!
