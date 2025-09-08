# Residencias Chable - Render.com Deployment Guide

## 🚀 Quick Start

### 1. **Prepare Your Repository**
- Ensure your code is pushed to GitHub/GitLab
- Make sure `env.example` file is in your repository
- Verify `requirements.txt` is up to date

### 2. **Create Render Service**
1. Go to [Render.com](https://render.com) and sign in
2. Click "New +" → "Web Service"
3. Connect your repository
4. Choose your Residencias Chable repository

### 3. **Configure Service Settings**

#### **Basic Settings:**
- **Name**: `residencias-chable-ai`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`

#### **Advanced Settings:**
- **Auto-Deploy**: `Yes` (for automatic deployments)
- **Branch**: `main` (or your production branch)

### 4. **Set Environment Variables**

In the Render dashboard, go to your service → **Environment** tab and add these variables:

#### **🔑 Required Variables (Minimum)**
```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-actual-openai-api-key-here

# Twilio Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-actual-twilio-auth-token
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890

# Database (Render will provide this if you create a PostgreSQL service)
DATABASE_URL=postgresql://username:password@host:port/database_name

# Application Settings
ENVIRONMENT=production
DEBUG=false
STORE_ID=residencias_chable_production
```

#### **🔧 Optional Variables (Recommended)**
```bash
# HubSpot Integration
HUBSPOT_API_KEY=your-hubspot-api-key

# Security
SECRET_KEY=your-super-secret-production-key
JWT_SECRET=your-jwt-secret-key

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# Application URL (will be your Render URL)
APP_URL=https://your-service-name.onrender.com
```

### 5. **Create PostgreSQL Database (Recommended)**

1. In Render dashboard, click "New +" → "PostgreSQL"
2. **Name**: `residencias-chable-db`
3. **Database**: `residencias_chable`
4. **User**: `residencias_chable_user`
5. **Region**: Choose closest to your users
6. **Plan**: Start with Free tier, upgrade as needed

**Important**: Copy the `DATABASE_URL` from the database service and add it to your web service environment variables.

### 6. **Deploy and Test**

1. Click "Create Web Service"
2. Wait for the build to complete (5-10 minutes)
3. Your service will be available at: `https://your-service-name.onrender.com`

### 7. **Configure Twilio Webhook**

1. Go to your Twilio Console
2. Navigate to WhatsApp → Sandbox Settings
3. Set webhook URL to: `https://your-service-name.onrender.com/message`
4. Set HTTP method to: `POST`

## 📋 Environment Variables Checklist

### ✅ **Core Functionality**
- [ ] `OPENAI_API_KEY` - Your OpenAI API key
- [ ] `TWILIO_ACCOUNT_SID` - Twilio Account SID
- [ ] `TWILIO_AUTH_TOKEN` - Twilio Auth Token
- [ ] `TWILIO_WHATSAPP_NUMBER` - WhatsApp Business Number
- [ ] `DATABASE_URL` - PostgreSQL connection string

### ✅ **Application Settings**
- [ ] `ENVIRONMENT=production`
- [ ] `DEBUG=false`
- [ ] `STORE_ID=residencias_chable_production`
- [ ] `SECRET_KEY` - Strong secret key

### ✅ **Optional Integrations**
- [ ] `HUBSPOT_API_KEY` - For CRM integration
- [ ] `SENTRY_DSN` - For error tracking
- [ ] `APP_URL` - Your Render service URL

## 🔧 **Troubleshooting**

### **Common Issues:**

1. **Build Fails**
   - Check `requirements.txt` is complete
   - Verify Python version compatibility
   - Check build logs for specific errors

2. **Service Won't Start**
   - Verify start command is correct
   - Check environment variables are set
   - Review service logs

3. **Database Connection Issues**
   - Verify `DATABASE_URL` is correct
   - Check database service is running
   - Ensure database credentials are valid

4. **Twilio Webhook Not Working**
   - Verify webhook URL is accessible
   - Check Twilio webhook configuration
   - Test with Render service URL

### **Debug Steps:**

1. **Check Service Logs**
   - Go to your service → "Logs" tab
   - Look for error messages
   - Check startup sequence

2. **Test Endpoints**
   - Visit `https://your-service.onrender.com/` (should show testing interface)
   - Test webhook endpoint manually

3. **Environment Variables**
   - Verify all required variables are set
   - Check for typos in variable names
   - Ensure no extra spaces or quotes

## 🚀 **Production Optimization**

### **Performance Settings:**
```bash
# Increase worker processes
WORKERS=4

# Set production environment
ENVIRONMENT=production
DEBUG=false

# Enable logging
LOG_LEVEL=info
```

### **Security Settings:**
```bash
# Use strong secrets
SECRET_KEY=your-very-strong-secret-key-here
JWT_SECRET=your-jwt-secret-key

# Disable debug mode
DEBUG=false

# Set secure headers
SECURE_HEADERS=true
```

### **Monitoring:**
```bash
# Error tracking
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# Analytics
GOOGLE_ANALYTICS_ID=GA-XXXXXXXXX
```

## 📊 **Post-Deployment Checklist**

- [ ] Service is running and accessible
- [ ] Testing interface loads at root URL
- [ ] Database connection is working
- [ ] Twilio webhook is configured
- [ ] Environment variables are set correctly
- [ ] Error tracking is configured (if using Sentry)
- [ ] SSL certificate is active (automatic with Render)
- [ ] Custom domain is configured (if needed)

## 🔄 **Updates and Maintenance**

### **Deploying Updates:**
1. Push changes to your repository
2. Render will automatically deploy (if auto-deploy is enabled)
3. Monitor deployment logs
4. Test functionality after deployment

### **Database Migrations:**
1. Run migrations locally first
2. Test with production database copy
3. Deploy application changes
4. Run migrations on production

### **Monitoring:**
- Check service logs regularly
- Monitor error rates
- Set up alerts for critical issues
- Review performance metrics

## 💰 **Cost Optimization**

### **Free Tier Limits:**
- 750 hours/month (enough for small projects)
- Service sleeps after 15 minutes of inactivity
- Cold start takes ~30 seconds

### **Upgrade Considerations:**
- **Starter Plan ($7/month)**: Always-on service
- **Standard Plan ($25/month)**: Better performance
- **Pro Plan ($85/month)**: High availability

## 📞 **Support**

- **Render Documentation**: [render.com/docs](https://render.com/docs)
- **Render Support**: Available in dashboard
- **Community**: [Render Community Forum](https://community.render.com)

---

**🎉 Congratulations!** Your Residencias Chable AI handler should now be live on Render.com and ready to handle WhatsApp conversations for your real estate clients in the Riviera Maya!
