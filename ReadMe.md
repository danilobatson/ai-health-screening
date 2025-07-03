# 🏥 AI Healthcare Assessment System

<!-- CI/CD Status Badges -->
[![CI/CD Pipeline](https://github.com/yourusername/ai-health-screening/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/yourusername/ai-health-screening/actions/workflows/ci-cd.yml)
[![Security Scan](https://github.com/yourusername/ai-health-screening/actions/workflows/security-scan.yml/badge.svg)](https://github.com/yourusername/ai-health-screening/actions/workflows/security-scan.yml)
[![Code Quality](https://github.com/yourusername/ai-health-screening/actions/workflows/code-quality.yml/badge.svg)](https://github.com/yourusername/ai-health-screening/actions/workflows/code-quality.yml)
[![Deployment](https://github.com/yourusername/ai-health-screening/actions/workflows/deployment.yml/badge.svg)](https://github.com/yourusername/ai-health-screening/actions/workflows/deployment.yml)

<!-- Coverage and Quality Badges -->
[![Backend Coverage](https://codecov.io/gh/yourusername/ai-health-screening/branch/main/graph/badge.svg?flag=backend)](https://codecov.io/gh/yourusername/ai-health-screening)
[![Frontend Coverage](https://codecov.io/gh/yourusername/ai-health-screening/branch/main/graph/badge.svg?flag=frontend)](https://codecov.io/gh/yourusername/ai-health-screening)
[![Code Quality Grade](https://img.shields.io/codefactor/grade/github/yourusername/ai-health-screening?label=Code%20Quality)](https://www.codefactor.io/repository/github/yourusername/ai-health-screening)

<!-- Tech Stack Badges -->
[![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat&logo=python)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?style=flat&logo=next.js)](https://nextjs.org)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat&logo=react)](https://reactjs.org)
[![Mantine](https://img.shields.io/badge/Mantine-UI-339AF0?style=flat&logo=mantine)](https://mantine.dev)

<!-- Deployment and Demo Badges -->
[![Deploy with Vercel](https://vercel.com/button)](https://ai-health-screening.vercel.app)
[![Live Demo](https://img.shields.io/badge/Live-Demo-00C7B7?style=flat&logo=vercel&logoColor=white)](https://ai-health-screening.vercel.app)

> **Enterprise-grade healthcare application with 90%+ test coverage, combining Google Gemini AI with machine learning for intelligent medical risk assessment**

## 🎯 Live Demo
**🚀 [Try it now: ai-health-screening.vercel.app](https://ai-health-screening.vercel.app)**

---

## 🏆 Project Highlights

### **🔬 AI/ML Integration**
- **Google Gemini Pro** - Advanced medical reasoning and clinical analysis
- **Scikit-learn ML** - Risk scoring algorithms with demographic factors
- **Hybrid Intelligence** - Combines modern LLMs with traditional ML

### **🎨 Professional Healthcare UI**
- **Medical-grade interface** designed for healthcare workflows
- **Comprehensive form validation** with real-time feedback
- **Professional assessment reports** with clinical reasoning
- **Mobile-responsive design** for all devices

### **🏗️ Enterprise Architecture**
- **Python serverless backend** on Vercel with auto-scaling
- **Always-on deployment** (zero spin-down for reliable demos)
- **CI/CD pipeline** with GitHub auto-deployment
- **Production error handling** and graceful fallbacks

---

## 🛠️ Tech Stack

### **Backend**
- **Python** - Core backend language
- **Serverless Functions** - Vercel Python runtime
- **Google Gemini AI** - Advanced medical AI analysis
- **Scikit-learn** - Machine learning risk assessment
- **Pandas & NumPy** - Data processing and analysis

### **Frontend**
- **Next.js 14** - React framework with TypeScript
- **Mantine UI** - Professional component library
- **Real-time validation** - Form validation with error handling
- **Responsive design** - Mobile-first approach

### **Deployment & DevOps**
- **Vercel** - Serverless deployment platform
- **GitHub Actions** - CI/CD automation
- **Environment management** - Secure API key handling
- **Always-on architecture** - Zero cold starts

---

## 🏥 Features

### **Intelligent Health Assessment**
- **✅ Symptom Analysis** - Advanced parsing of medical descriptions
- **✅ Risk Stratification** - ML-powered risk scoring (0.0-1.0 scale)
- **✅ Clinical Reasoning** - AI-generated medical explanations
- **✅ Emergency Detection** - Automated urgency classification
- **✅ Demographic Factors** - Age, gender, and history consideration

### **Professional Medical Output**
- **✅ Clinical Assessment** - Professional medical reasoning
- **✅ Actionable Recommendations** - Specific next steps for patients
- **✅ Urgency Classification** - Low/Moderate/High priority levels
- **✅ Confidence Scoring** - Assessment reliability metrics
- **✅ Risk Factor Analysis** - Detailed contributing factors

### **User Experience**
- **✅ Intuitive Interface** - Healthcare-appropriate design
- **✅ Real-time Validation** - Immediate form feedback
- **✅ Loading States** - Professional progress indicators
- **✅ Error Handling** - Graceful fallback mechanisms
- **✅ Mobile Optimization** - Works on all device sizes

---

## 🚀 Quick Start

### **Try the Live Demo**
Visit **[ai-health-screening.vercel.app](https://ai-health-screening.vercel.app)** for an immediate demonstration.

### **Local Development**
```bash
# Clone repository
git clone https://github.com/danilobatson/ai-health-screening.git
cd ai-health-screening

# Frontend setup
cd frontend
npm install
npm run dev

# Backend setup (in separate terminal)
cd ../
pip install -r requirements.txt
# Add your GEMINI_API_KEY to .env
uvicorn main:app --reload
```

## Environment Variables

```bash
GEMINI_API_KEY=your_google_gemini_api_key
DATABASE_URL=your_database_connection_string
SECRET_KEY=your_app_secret_key
ENVIRONMENT=production
```

## 📊 Architecture Overview


```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Next.js App   │───▶│  Vercel Python   │───▶│  Google Gemini  │
│   (Frontend)    │    │   (Backend)      │    │      AI         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌──────────────────┐             │
         │              │  Scikit-learn    │             │
         │              │  ML Algorithms   │             │
         │              └──────────────────┘             │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              Professional Medical Assessment                     │
│    Clinical Reasoning + Risk Scoring + Recommendations          │
└─────────────────────────────────────────────────────────────────┘
```

## 🧪 Try It Out

Visit the [live demo.](ai-health-screening.vercel.app)
Fill out the health assessment form with symptoms
Get AI-powered analysis with risk scoring and recommendations
Experience professional medical UI designed for healthcare
# Test commit: Wed Jul  2 21:40:57 PDT 2025
