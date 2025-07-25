import React, { useState, useEffect, createContext, useContext } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { 
  MessageSquare, 
  Clock, 
  CheckCircle, 
  User, 
  CreditCard, 
  LogOut, 
  Crown, 
  Building2, 
  Calendar,
  Repeat,
  Trash2,
  Bell,
  Wand2,
  Sparkles,
  RefreshCw,
  Send,
  Lightbulb,
  Shield,
  DollarSign,
  TrendingUp,
  Users,
  FileText,
  Download,
  Settings,
  Share,
  Gift,
  Copy,
  BarChart3,
  PieChart,
  LineChart,
  Activity,
  Target,
  Zap,
  Brain,
  Eye,
  Filter,
  Archive,
  Globe
} from "lucide-react";
import "./App.css";
import axios from "axios";
import { useTranslation, LanguageContext } from "./translations";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Context for authentication
const AuthContext = createContext();

// Auth Provider Component
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUser();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { email, password });
    const { access_token, user: userData } = response.data;
    localStorage.setItem('token', access_token);
    axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    setUser(userData);
    return userData;
  };

  const register = async (email, password, name, referralCode = '') => {
    const response = await axios.post(`${API}/auth/register`, { 
      email, 
      password, 
      name, 
      referral_code: referralCode 
    });
    const { access_token, user: userData } = response.data;
    localStorage.setItem('token', access_token);
    axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    setUser(userData);
    return userData;
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
  };

  const value = {
    user,
    login,
    register,
    logout,
    loading,
    refreshUser: fetchUser
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Language Provider Component
const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState(() => {
    // Get language from localStorage or default to German
    const savedLang = localStorage.getItem('language');
    return savedLang || 'de';
  });

  const { t } = useTranslation(language);

  const switchLanguage = (newLang) => {
    setLanguage(newLang);
    localStorage.setItem('language', newLang);
  };

  const value = {
    language,
    setLanguage: switchLanguage,
    t
  };

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
};

// Language Switcher Component
const LanguageSwitcher = () => {
  const { language, setLanguage, t } = useContext(LanguageContext);
  
  return (
    <div className="relative">
      <button
        onClick={() => setLanguage(language === 'de' ? 'en' : 'de')}
        className="flex items-center space-x-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
        title={t('lang.switch')}
      >
        <Globe className="w-4 h-4" />
        <span>{language === 'de' ? t('lang.german') : t('lang.english')}</span>
      </button>
    </div>
  );
};

// Login/Register Component
const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ email: '', password: '', name: '', referralCode: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login, register } = useAuth();
  const { t } = useContext(LanguageContext);

  useEffect(() => {
    // Check for referral code in URL
    const urlParams = new URLSearchParams(window.location.search);
    const refCode = urlParams.get('ref');
    if (refCode) {
      setFormData(prev => ({ ...prev, referralCode: refCode }));
      setIsLogin(false); // Switch to registration for referrals
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (isLogin) {
        await login(formData.email, formData.password);
      } else {
        await register(formData.email, formData.password, formData.name, formData.referralCode);
      }
    } catch (error) {
      setError(error.response?.data?.detail || t('message.error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-lg p-8 w-full max-w-md">
        {/* Language Switcher */}
        <div className="flex justify-end mb-4">
          <LanguageSwitcher />
        </div>

        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            ⏰ {t('app.title')}
          </h1>
          <p className="text-gray-600">
            {isLogin ? t('auth.login') : t('auth.register')}
          </p>
        </div>

        {error && (
          <div className="bg-red-50 text-red-700 p-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('auth.name')}
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder={t('auth.name')}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('auth.referralCode')}
                </label>
                <input
                  type="text"
                  value={formData.referralCode}
                  onChange={(e) => setFormData({...formData, referralCode: e.target.value.toUpperCase()})}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  placeholder="Z.B. ABC123XY"
                  maxLength="8"
                />
                {formData.referralCode && (
                  <p className="text-xs text-green-600 mt-1">
                    {t('auth.referralBonus')}
                  </p>
                )}
              </div>
            </>
          )}
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('auth.email')}
            </label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder={t('auth.email').toLowerCase() + "@example.com"}
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('auth.password')}
            </label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="••••••••"
              required
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-500 hover:bg-blue-600 text-white font-medium py-3 px-6 rounded-lg transition-colors disabled:opacity-50"
          >
            {loading ? t('action.loading') : (isLogin ? t('auth.loginButton') : t('auth.registerButton'))}
          </button>
        </form>

        <div className="text-center mt-6">
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-blue-500 hover:text-blue-600"
          >
            {isLogin ? t('auth.switchToRegister') : t('auth.switchToLogin')}
          </button>
        </div>
      </div>
    </div>
  );
};

// Header Component
const Header = ({ activeTab, setActiveTab }) => {
  const { user, logout } = useAuth();
  const { t } = useContext(LanguageContext);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const getPlanIcon = (plan) => {
    switch(plan) {
      case 'premium': return <Crown className="w-4 h-4 text-yellow-500" />;
      case 'business': return <Building2 className="w-4 h-4 text-purple-500" />;
      default: return <User className="w-4 h-4 text-gray-500" />;
    }
  };

  const getPlanColor = (plan) => {
    switch(plan) {
      case 'premium': return 'bg-yellow-50 text-yellow-700 border-yellow-200';
      case 'business': return 'bg-purple-50 text-purple-700 border-purple-200';
      default: return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-6xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold text-gray-800">
              ⏰ {t('app.title')}
            </h1>
            <div className={`flex items-center space-x-2 px-3 py-1 rounded-full border ${getPlanColor(user.subscription_plan)}`}>
              {getPlanIcon(user.subscription_plan)}
              <span className="text-sm font-medium capitalize">{t('plans.' + user.subscription_plan)}</span>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <LanguageSwitcher />
            
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center space-x-2 px-4 py-2 text-gray-700 hover:text-gray-900 hover:bg-gray-50 rounded-lg transition-colors"
              >
                <User className="w-5 h-5" />
                <span className="hidden md:inline">{user.name}</span>
              </button>

              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
                  <div className="p-4 border-b border-gray-200">
                    <p className="font-medium text-gray-900">{user.name}</p>
                    <p className="text-sm text-gray-600">{user.email}</p>
                    <div className="mt-2">
                      <div className="text-xs text-gray-500">{t('plans.messagesUsed')}</div>
                      <div className="text-sm font-medium">
                        {user.monthly_messages_limit === -1 ? 
                          `${user.monthly_messages_used} (${t('plans.unlimited')})` :
                          `${user.monthly_messages_used} / ${user.monthly_messages_limit}`
                        }
                      </div>
                    </div>
                  </div>
                  <div className="p-2">
                    <button
                      onClick={() => {
                        setActiveTab('subscription');
                        setShowUserMenu(false);
                      }}
                      className="w-full flex items-center space-x-2 px-3 py-2 text-left text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
                    >
                      <CreditCard className="w-4 h-4" />
                      <span>{t('nav.subscription')}</span>
                    </button>
                    {user.role === 'admin' && (
                      <button
                        onClick={() => {
                          setActiveTab('admin');
                          setShowUserMenu(false);
                        }}
                        className="w-full flex items-center space-x-2 px-3 py-2 text-left text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
                      >
                        <Shield className="w-4 h-4" />
                        <span>{t('nav.admin')}</span>
                      </button>
                    )}
                    <button
                      onClick={logout}
                      className="w-full flex items-center space-x-2 px-3 py-2 text-left text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>{t('auth.logout')}</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

// Main Dashboard Component
const Dashboard = () => {
  const { t } = useContext(LanguageContext);
  const [messages, setMessages] = useState([]);
  const [activeTab, setActiveTab] = useState('create');
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    scheduled_time: '',
    is_recurring: false,
    recurring_pattern: ''
  });
  const [loading, setLoading] = useState(false);
  const [subscriptionPlans, setSubscriptionPlans] = useState({});
  const [aiSuggestions, setSuggestions] = useState([]);
  const [aiLoading, setAiLoading] = useState(false);
  const [showAiPanel, setShowAiPanel] = useState(false);
  const [adminStats, setAdminStats] = useState(null);
  const [adminData, setAdminData] = useState({
    users: [],
    transactions: [],
    payouts: []
  });
  const [payoutAmount, setPayoutAmount] = useState('');
  const [payoutLoading, setPayoutLoading] = useState(false);
  const [referralData, setReferralData] = useState(null);
  
  // Advanced Analytics State
  const [advancedAnalytics, setAdvancedAnalytics] = useState(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [selectedAnalyticsTab, setSelectedAnalyticsTab] = useState('overview');
  const [copySuccess, setCopySuccess] = useState(false);
  const { user, refreshUser } = useAuth();

  // Enhanced Messaging State
  const [messageMode, setMessageMode] = useState('single'); // 'single', 'bulk', 'template'
  const [bulkMessages, setBulkMessages] = useState([
    { title: '', content: '', scheduled_time: '', is_recurring: false, recurring_pattern: '' }
  ]);
  const [timeInterval, setTimeInterval] = useState(5);
  const [templates, setTemplates] = useState({ user_templates: [], public_templates: [] });
  const [templatesLoading, setTemplatesLoading] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [newTemplate, setNewTemplate] = useState({
    name: '',
    title: '',
    content: '',
    category: 'general',
    is_public: false
  });
  const [calendarDate, setCalendarDate] = useState(new Date());
  const [calendarData, setCalendarData] = useState(null);
  const [showCalendar, setShowCalendar] = useState(false);

  // Marketing Automation State  
  const [marketingCampaigns, setMarketingCampaigns] = useState([]);
  const [marketingTemplates, setMarketingTemplates] = useState({ predefined_templates: [], custom_templates: [] });
  const [socialPosts, setSocialPosts] = useState({ ready_to_use_posts: [], custom_posts: [] });
  const [launchMetrics, setLaunchMetrics] = useState(null);
  const [launchChecklist, setLaunchChecklist] = useState([]);
  const [marketingLoading, setMarketingLoading] = useState(false);
  const [selectedMarketingTab, setSelectedMarketingTab] = useState('overview');

  // Contact & Email Delivery Management State
  const [contactsOverview, setContactsOverview] = useState(null);
  const [emailDeliveriesOverview, setEmailDeliveriesOverview] = useState(null);
  const [allContacts, setAllContacts] = useState([]);
  const [recentDeliveries, setRecentDeliveries] = useState([]);
  const [contactManagementLoading, setContactManagementLoading] = useState(false);
  const [selectedContactTab, setSelectedContactTab] = useState('overview');
  const [contactSearchTerm, setContactSearchTerm] = useState('');
  const [contactTypeFilter, setContactTypeFilter] = useState('');
  const [deliveryStatusFilter, setDeliveryStatusFilter] = useState('');

  // Fetch messages
  const fetchMessages = async () => {
    try {
      const response = await axios.get(`${API}/messages`);
      setMessages(response.data);
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
  };

  // Fetch subscription plans
  const fetchSubscriptionPlans = async () => {
    try {
      const response = await axios.get(`${API}/subscriptions/plans`);
      setSubscriptionPlans(response.data);
    } catch (error) {
      console.error('Error fetching plans:', error);
    }
  };

  // Fetch AI suggestions
  const fetchAiSuggestions = async () => {
    try {
      const response = await axios.get(`${API}/ai/suggestions`);
      setSuggestions(response.data.suggestions || []);
    } catch (error) {
      console.error('Error fetching AI suggestions:', error);
    }
  };

  // Fetch admin statistics
  const fetchAdminStats = async () => {
    if (user?.role !== 'admin') return;
    
    try {
      const response = await axios.get(`${API}/admin/stats`);
      setAdminStats(response.data);
    } catch (error) {
      console.error('Error fetching admin stats:', error);
    }
  };

  // Fetch admin data
  const fetchAdminData = async () => {
    if (user?.role !== 'admin') return;
    
    try {
      const [usersRes, transactionsRes, payoutsRes] = await Promise.all([
        axios.get(`${API}/admin/users`),
        axios.get(`${API}/admin/transactions`),
        axios.get(`${API}/admin/payouts`)
      ]);

      setAdminData({
        users: usersRes.data.users || [],
        transactions: transactionsRes.data.transactions || [],
        payouts: payoutsRes.data.payouts || []
      });
    } catch (error) {
      console.error('Error fetching admin data:', error);
    }
  };

  // Fetch referral data
  const fetchReferralData = async () => {
    try {
      const response = await axios.get(`${API}/auth/referrals`);
      setReferralData(response.data);
    } catch (error) {
      console.error('Error fetching referral data:', error);
    }
  };

  // Fetch advanced analytics data
  const fetchAdvancedAnalytics = async () => {
    if (user?.role !== 'admin') return;
    
    setAnalyticsLoading(true);
    try {
      const response = await axios.get(`${API}/admin/analytics/complete`);
      setAdvancedAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching advanced analytics:', error);
      setAdvancedAnalytics(null);
    } finally {
      setAnalyticsLoading(false);
    }
  };

  // Export analytics data
  const exportAnalytics = async (format) => {
    if (user?.role !== 'admin') return;
    
    try {
      const response = await axios.get(`${API}/admin/analytics/export?format=${format}`);
      
      if (format === 'json') {
        const dataStr = JSON.stringify(response.data, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
        const exportFileDefaultName = `analytics-export-${new Date().toISOString().split('T')[0]}.json`;
        
        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', exportFileDefaultName);
        linkElement.click();
      } else {
        // CSV export would be handled by the backend in a real implementation
        alert('CSV Export vorbereitet. In einer echten Implementierung würde eine CSV-Datei heruntergeladen.');
      }
    } catch (error) {
      console.error('Error exporting analytics:', error);
      alert('Fehler beim Exportieren der Daten');
    }
  };

  // Enhanced Messaging Functions
  const fetchTemplates = async () => {
    setTemplatesLoading(true);
    try {
      const response = await axios.get(`${API}/templates`);
      setTemplates(response.data);
    } catch (error) {
      console.error('Error fetching templates:', error);
      setTemplates({ user_templates: [], public_templates: [] });
    } finally {
      setTemplatesLoading(false);
    }
  };

  const createTemplate = async (templateData) => {
    try {
      await axios.post(`${API}/templates`, templateData);
      fetchTemplates(); // Refresh templates list
      setShowTemplateModal(false);
      setNewTemplate({ name: '', title: '', content: '', category: 'general', is_public: false });
      alert(t ? t('message.templateCreated') : 'Template erfolgreich erstellt!');
    } catch (error) {
      console.error('Error creating template:', error);
      alert(t ? t('message.error') : 'Fehler beim Erstellen der Vorlage');
    }
  };

  const useTemplate = async (templateId) => {
    try {
      const response = await axios.post(`${API}/templates/${templateId}/use`);
      const templateData = response.data;
      
      if (messageMode === 'bulk') {
        // Add template data to first bulk message
        setBulkMessages(prev => prev.map((msg, index) => 
          index === 0 
            ? { ...msg, title: templateData.title, content: templateData.content }
            : msg
        ));
      } else {
        // Single message mode
        setFormData(prev => ({
          ...prev,
          title: templateData.title,
          content: templateData.content
        }));
      }
      
      alert(t ? t('message.templateUsed') : 'Vorlage angewendet!');
    } catch (error) {
      console.error('Error using template:', error);
      alert(t ? t('message.error') : 'Fehler beim Verwenden der Vorlage');
    }
  };

  const createBulkMessages = async () => {
    if (!user) return;
    
    if (user.subscription_plan === 'free') {
      alert(t ? t('message.bulkRequiresPremium') : 'Bulk-Nachrichten sind nur für Premium- und Business-Nutzer verfügbar.');
      return;
    }

    setLoading(true);
    try {
      const bulkRequest = {
        messages: bulkMessages.filter(msg => msg.title && msg.content && msg.scheduled_time),
        time_interval: timeInterval
      };

      if (bulkRequest.messages.length === 0) {
        alert(t ? t('message.fillAllFields') : 'Bitte füllen Sie alle erforderlichen Felder aus.');
        setLoading(false);
        return;
      }

      const response = await axios.post(`${API}/messages/bulk`, bulkRequest);
      
      alert(t ? t('message.bulkCreated', { count: response.data.success_count }) : 
            `${response.data.success_count} Nachrichten erfolgreich erstellt!`);
      
      // Reset form
      setBulkMessages([{ title: '', content: '', scheduled_time: '', is_recurring: false, recurring_pattern: '' }]);
      setMessageMode('single');
      fetchMessages();
      refreshUser();
    } catch (error) {
      console.error('Error creating bulk messages:', error);
      alert(error.response?.data?.detail || (t ? t('message.error') : 'Fehler beim Erstellen der Nachrichten'));
    } finally {
      setLoading(false);
    }
  };

  const addBulkMessage = () => {
    setBulkMessages(prev => [...prev, {
      title: '', content: '', scheduled_time: '', is_recurring: false, recurring_pattern: ''
    }]);
  };

  const removeBulkMessage = (index) => {
    setBulkMessages(prev => prev.filter((_, i) => i !== index));
  };

  const updateBulkMessage = (index, field, value) => {
    setBulkMessages(prev => prev.map((msg, i) => 
      i === index ? { ...msg, [field]: value } : msg
    ));
  };

  const fetchCalendarData = async (year, month) => {
    try {
      const response = await axios.get(`${API}/messages/calendar/${year}/${month}`);
      setCalendarData(response.data);
    } catch (error) {
      console.error('Error fetching calendar data:', error);
      setCalendarData(null);
    }
  };

  // Marketing Automation Functions
  const fetchMarketingData = async () => {
    if (user?.role !== 'admin') return;
    
    setMarketingLoading(true);
    try {
      // Fetch all marketing data in parallel
      const [campaignsRes, templatesRes, postsRes, metricsRes, checklistRes] = await Promise.all([
        axios.get(`${API}/admin/marketing/campaigns`),
        axios.get(`${API}/admin/marketing/templates`),
        axios.get(`${API}/admin/marketing/social-posts`),
        axios.get(`${API}/admin/marketing/launch-metrics`),
        axios.get(`${API}/admin/marketing/launch-checklist`)
      ]);
      
      setMarketingCampaigns(campaignsRes.data.campaigns || []);
      setMarketingTemplates(templatesRes.data);
      setSocialPosts(postsRes.data);
      setLaunchMetrics(metricsRes.data);
      setLaunchChecklist(checklistRes.data.checklist || []);
      
    } catch (error) {
      console.error('Error fetching marketing data:', error);
    } finally {
      setMarketingLoading(false);
    }
  };

  const createMarketingCampaign = async (campaignData) => {
    if (user?.role !== 'admin') return;
    
    try {
      await axios.post(`${API}/admin/marketing/campaigns`, campaignData);
      fetchMarketingData(); // Refresh data
      alert('Marketing-Kampagne erfolgreich erstellt!');
    } catch (error) {
      console.error('Error creating marketing campaign:', error);
      alert('Fehler beim Erstellen der Kampagne');
    }
  };

  const scheduleSocialPost = async (postData) => {
    if (user?.role !== 'admin') return;
    
    try {
      await axios.post(`${API}/admin/marketing/social-posts`, postData);
      fetchMarketingData(); // Refresh data
      alert('Social Media Post erfolgreich geplant!');
    } catch (error) {
      console.error('Error scheduling social post:', error);
      alert('Fehler beim Planen des Posts');
    }
  };

  // Contact & Email Delivery Management Functions
  const fetchContactManagementData = async () => {
    if (user?.role !== 'admin') return;
    
    setContactManagementLoading(true);
    try {
      // Fetch all contact management data in parallel
      const [contactsRes, emailDeliveriesRes, allContactsRes, recentDeliveriesRes] = await Promise.all([
        axios.get(`${API}/admin/contacts/overview`),
        axios.get(`${API}/admin/email-deliveries/overview`),
        axios.get(`${API}/admin/contacts/all?limit=20`),
        axios.get(`${API}/admin/email-deliveries/recent?limit=20`)
      ]);
      
      setContactsOverview(contactsRes.data);
      setEmailDeliveriesOverview(emailDeliveriesRes.data);
      setAllContacts(allContactsRes.data.contacts || []);
      setRecentDeliveries(recentDeliveriesRes.data.deliveries || []);
      
    } catch (error) {
      console.error('Error fetching contact management data:', error);
    } finally {
      setContactManagementLoading(false);
    }
  };

  const searchContacts = async (searchTerm, contactType) => {
    if (user?.role !== 'admin') return;
    
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (contactType) params.append('contact_type', contactType);
      params.append('limit', '50');
      
      const response = await axios.get(`${API}/admin/contacts/all?${params}`);
      setAllContacts(response.data.contacts || []);
    } catch (error) {
      console.error('Error searching contacts:', error);
    }
  };

  const filterDeliveries = async (status) => {
    if (user?.role !== 'admin') return;
    
    try {
      const params = new URLSearchParams();
      if (status) params.append('status', status);
      params.append('limit', '50');
      
      const response = await axios.get(`${API}/admin/email-deliveries/recent?${params}`);
      setRecentDeliveries(response.data.deliveries || []);
    } catch (error) {
      console.error('Error filtering deliveries:', error);
    }
  };

  const mergeContacts = async (sourceContactId, targetContactId) => {
    if (user?.role !== 'admin') return;
    
    try {
      await axios.post(`${API}/admin/contacts/${sourceContactId}/merge`, {
        target_contact_id: targetContactId
      });
      fetchContactManagementData(); // Refresh data
      alert('Kontakte erfolgreich zusammengeführt!');
    } catch (error) {
      console.error('Error merging contacts:', error);
      alert('Fehler beim Zusammenführen der Kontakte');
    }
  };

  // Copy referral link
  const copyReferralLink = async () => {
    if (referralData?.referral_link) {
      try {
        await navigator.clipboard.writeText(referralData.referral_link);
        setCopySuccess(true);
        setTimeout(() => setCopySuccess(false), 2000);
      } catch (error) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = referralData.referral_link;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        setCopySuccess(true);
        setTimeout(() => setCopySuccess(false), 2000);
      }
    }
  };

  // Request payout
  const requestPayout = async () => {
    const amount = parseFloat(payoutAmount);
    if (!amount || amount <= 0) {
      alert('Bitte geben Sie einen gültigen Betrag ein');
      return;
    }

    setPayoutLoading(true);
    try {
      await axios.post(`${API}/admin/payout`, {
        amount,
        description: `Admin payout request - €${amount}`
      });
      
      setPayoutAmount('');
      fetchAdminStats();
      fetchAdminData();
      fetchAdvancedAnalytics();
      alert(`Auszahlung von €${amount} wurde erfolgreich angefordert!`);
    } catch (error) {
      alert(error.response?.data?.detail || 'Fehler bei der Auszahlungsanforderung');
    } finally {
      setPayoutLoading(false);
    }
  };

  // Generate message with AI
  const generateMessageWithAI = async (prompt, tone = "freundlich", occasion = null) => {
    setAiLoading(true);
    try {
      const response = await axios.post(`${API}/ai/generate`, {
        prompt,
        tone,
        occasion
      });
      
      if (response.data.success) {
        return response.data.generated_text;
      } else {
        throw new Error(response.data.error || 'AI-Generierung fehlgeschlagen');
      }
    } catch (error) {
      console.error('Error generating AI message:', error);
      alert(error.response?.data?.detail || 'AI-Generierung fehlgeschlagen');
      return null;
    } finally {
      setAiLoading(false);
    }
  };

  // Enhance message with AI
  const enhanceMessageWithAI = async (text, action, tone = "freundlich") => {
    setAiLoading(true);
    try {
      const response = await axios.post(`${API}/ai/enhance`, {
        text,
        action,
        tone
      });
      
      if (response.data.success) {
        return response.data.generated_text;
      } else {
        throw new Error(response.data.error || 'AI-Verbesserung fehlgeschlagen');
      }
    } catch (error) {
      console.error('Error enhancing message:', error);
      alert(error.response?.data?.detail || 'AI-Verbesserung fehlgeschlagen');
      return null;
    } finally {
      setAiLoading(false);
    }
  };

  // Use AI suggestion
  const useAiSuggestion = async (suggestion) => {
    const generatedContent = await generateMessageWithAI(
      suggestion.prompt, 
      suggestion.tone, 
      suggestion.occasion
    );
    
    if (generatedContent) {
      // Extract title from first line or create one
      const lines = generatedContent.split('\n').filter(line => line.trim());
      const title = lines[0].length > 50 ? 
        lines[0].substring(0, 47) + '...' : 
        lines[0];
      const content = lines.length > 1 ? lines.slice(1).join('\n').trim() : generatedContent;
      
      setFormData({
        ...formData,
        title: title.replace(/['"]/g, ''),
        content: content || generatedContent
      });
      setShowAiPanel(false);
    }
  };

  // Create new message
  const createMessage = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const messageData = {
        ...formData,
        scheduled_time: new Date(formData.scheduled_time).toISOString()
      };
      
      await axios.post(`${API}/messages`, messageData);
      setFormData({ 
        title: '', 
        content: '', 
        scheduled_time: '',
        is_recurring: false,
        recurring_pattern: ''
      });
      fetchMessages();
      refreshUser(); // Refresh user data to update message count
      setActiveTab('scheduled');
    } catch (error) {
      console.error('Error creating message:', error);
      alert(error.response?.data?.detail || 'Fehler beim Erstellen der Nachricht!');
    } finally {
      setLoading(false);
    }
  };

  // Delete message
  const deleteMessage = async (messageId) => {
    try {
      await axios.delete(`${API}/messages/${messageId}`);
      fetchMessages();
      refreshUser(); // Refresh user data
    } catch (error) {
      console.error('Error deleting message:', error);
    }
  };

  // Subscribe to plan
  const subscribeToPlan = async (planName) => {
    try {
      const response = await axios.post(`${API}/subscriptions/subscribe`, { plan: planName });
      window.location.href = response.data.checkout_url;
    } catch (error) {
      console.error('Error subscribing:', error);
      alert(error.response?.data?.detail || 'Fehler beim Abonnieren!');
    }
  };

  // Get minimum date/time (now + 1 minute)
  const getMinDateTime = () => {
    const now = new Date();
    now.setMinutes(now.getMinutes() + 1);
    return now.toISOString().slice(0, 16);
  };

  // Format date for display
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('de-DE', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Filter messages by status
  const getMessagesByStatus = (status) => {
    return messages.filter(message => message.status === status);
  };

  // Check if message is due soon (within 2 minutes)
  const isMessageDueSoon = (scheduledTime) => {
    const now = new Date();
    const scheduled = new Date(scheduledTime);
    const diffMinutes = (scheduled - now) / (1000 * 60);
    return diffMinutes <= 2 && diffMinutes > 0;
  };

  const canUseRecurring = user?.subscription_plan !== 'free';
  const isAtMessageLimit = user?.monthly_messages_limit !== -1 && 
                          user?.monthly_messages_used >= user?.monthly_messages_limit;

  useEffect(() => {
    fetchMessages();
    fetchSubscriptionPlans();
    fetchAiSuggestions();
    fetchReferralData();
    fetchTemplates();
    
    if (user?.role === 'admin') {
      fetchAdminStats();
      fetchAdminData();
      fetchAdvancedAnalytics();
      fetchMarketingData();
      fetchContactManagementData();
    }
    
    // Refresh messages every 10 seconds to show delivered messages
    const interval = setInterval(() => {
      fetchMessages();
      if (user?.role === 'admin') {
        fetchAdminStats();
      }
    }, 10000);
    return () => clearInterval(interval);
  }, [user]);

  const scheduledMessages = getMessagesByStatus('scheduled');
  const deliveredMessages = getMessagesByStatus('delivered');

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Tab Navigation */}
        <div className="bg-white rounded-xl shadow-lg p-2 mb-6">
          <div className="flex space-x-1 overflow-x-auto">
            <button
              onClick={() => setActiveTab('create')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${
                activeTab === 'create'
                  ? 'bg-blue-500 text-white shadow-md'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <MessageSquare className="w-4 h-4 inline mr-2" />
              {t('nav.create')}
            </button>
            <button
              onClick={() => setActiveTab('scheduled')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${
                activeTab === 'scheduled'
                  ? 'bg-blue-500 text-white shadow-md'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Clock className="w-4 h-4 inline mr-2" />
              {t('nav.scheduled')} ({scheduledMessages.length})
            </button>
            <button
              onClick={() => setActiveTab('delivered')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${
                activeTab === 'delivered'
                  ? 'bg-blue-500 text-white shadow-md'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <CheckCircle className="w-4 h-4 inline mr-2" />
              {t('nav.delivered')} ({deliveredMessages.length})
            </button>
            <button
              onClick={() => setActiveTab('subscription')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${
                activeTab === 'subscription'
                  ? 'bg-blue-500 text-white shadow-md'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <CreditCard className="w-4 h-4 inline mr-2" />
              {t('nav.subscription')}
            </button>
            <button
              onClick={() => setActiveTab('referral')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${
                activeTab === 'referral'
                  ? 'bg-green-500 text-white shadow-md'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Share className="w-4 h-4 inline mr-2" />
              {t('nav.referral')}
              {user?.referred_count > 0 && (
                <span className="ml-1 bg-green-100 text-green-800 text-xs px-2 py-0.5 rounded-full">
                  {user.referred_count}
                </span>
              )}
            </button>
            {user?.role === 'admin' && (
              <button
                onClick={() => setActiveTab('admin')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${
                  activeTab === 'admin'
                    ? 'bg-purple-500 text-white shadow-md'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <Shield className="w-4 h-4 inline mr-2" />
                {t('nav.admin')}
              </button>
            )}
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'create' && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-semibold text-gray-800">
                {t('create.title')}
              </h2>
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => setShowCalendar(!showCalendar)}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
                >
                  <Calendar className="w-4 h-4" />
                  <span>Kalender</span>
                </button>
                <button
                  onClick={() => setShowTemplateModal(true)}
                  className="flex items-center space-x-2 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors"
                >
                  <FileText className="w-4 h-4" />
                  <span>Vorlagen</span>
                </button>
                <button
                  onClick={() => setShowAiPanel(!showAiPanel)}
                  className="flex items-center space-x-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg transition-colors"
                >
                  <Wand2 className="w-4 h-4" />
                  <span>{t('ai.assistant')}</span>
                </button>
              </div>
            </div>

            {/* Message Creation Mode Selector */}
            <div className="mb-6">
              <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setMessageMode('single')}
                  className={`flex-1 px-4 py-2 rounded-md font-medium transition-colors ${
                    messageMode === 'single'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <MessageSquare className="w-4 h-4 inline mr-2" />
                  Einzelnachricht
                </button>
                {user?.subscription_plan !== 'free' && (
                  <button
                    onClick={() => setMessageMode('bulk')}
                    className={`flex-1 px-4 py-2 rounded-md font-medium transition-colors ${
                      messageMode === 'bulk'
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    <Archive className="w-4 h-4 inline mr-2" />
                    Bulk-Nachrichten
                    <Crown className="w-3 h-3 inline ml-1 text-yellow-500" />
                  </button>
                )}
              </div>
              {user?.subscription_plan === 'free' && (
                <p className="text-xs text-gray-500 mt-2">
                  💡 Bulk-Nachrichten sind für Premium- und Business-Nutzer verfügbar
                </p>
              )}
            </div>

            {/* AI Assistant Panel */}
            {showAiPanel && (
              <div className="bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-lg p-4 mb-6">
                <div className="flex items-center space-x-2 mb-4">
                  <Sparkles className="w-5 h-5 text-purple-600" />
                  <h3 className="font-semibold text-purple-800">AI-Nachrichtenassistent</h3>
                </div>
                
                {aiLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <RefreshCw className="w-6 h-6 text-purple-600 animate-spin mr-2" />
                    <span className="text-purple-700">AI generiert Nachricht...</span>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <p className="text-sm text-purple-700 mb-3">
                      Wählen Sie eine Vorlage oder beschreiben Sie, welche Nachricht Sie benötigen:
                    </p>
                    
                    <div className="grid md:grid-cols-2 gap-2 mb-4">
                      {aiSuggestions.map((suggestion, index) => (
                        <button
                          key={index}
                          onClick={() => useAiSuggestion(suggestion)}
                          className="text-left p-3 bg-white border border-purple-200 hover:border-purple-300 hover:bg-purple-50 rounded-lg transition-colors text-sm"
                        >
                          <div className="flex items-start space-x-2">
                            <Lightbulb className="w-4 h-4 text-purple-500 mt-0.5 flex-shrink-0" />
                            <span className="text-gray-700">{suggestion.prompt}</span>
                          </div>
                          <div className="mt-1 flex items-center space-x-2 text-xs">
                            <span className="text-purple-600 capitalize">{suggestion.tone}</span>
                            {suggestion.occasion && (
                              <>
                                <span className="text-gray-400">•</span>
                                <span className="text-gray-600 capitalize">{suggestion.occasion}</span>
                              </>
                            )}
                          </div>
                        </button>
                      ))}
                    </div>

                    <div className="border-t border-purple-200 pt-3">
                      <div className="flex space-x-2">
                        <input
                          type="text"
                          placeholder="Eigenen Prompt eingeben..."
                          className="flex-1 px-3 py-2 border border-purple-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                          onKeyPress={(e) => {
                            if (e.key === 'Enter' && e.target.value.trim()) {
                              useAiSuggestion({
                                prompt: e.target.value,
                                tone: "freundlich",
                                occasion: null
                              });
                              e.target.value = '';
                            }
                          }}
                        />
                        <button
                          onClick={(e) => {
                            const input = e.target.previousElementSibling;
                            if (input.value.trim()) {
                              useAiSuggestion({
                                prompt: input.value,
                                tone: "freundlich",
                                occasion: null
                              });
                              input.value = '';
                            }
                          }}
                          className="px-3 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg transition-colors"
                        >
                          <Send className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {isAtMessageLimit && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
                <div className="flex items-center space-x-2">
                  <Bell className="w-5 h-5 text-yellow-600" />
                  <div>
                    <p className="font-medium text-yellow-800">{t('message.limitReached')}</p>
                    <p className="text-sm text-yellow-700">
                      {t('message.upgradeRequired', { limit: user.monthly_messages_limit })}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Single Message Form */}
            {messageMode === 'single' && (
              <form onSubmit={createMessage} className="space-y-6">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700">
                      {t('create.messageTitle')}
                    </label>
                    {formData.title && (
                      <div className="flex space-x-2">
                        <button
                          type="button"
                          onClick={async () => {
                            const enhanced = await enhanceMessageWithAI(formData.title, "improve");
                            if (enhanced) setFormData({...formData, title: enhanced});
                          }}
                          className="text-xs text-purple-600 hover:text-purple-800 flex items-center space-x-1"
                        >
                          <Wand2 className="w-3 h-3" />
                          <span>{t('ai.improve')}</span>
                        </button>
                        <button
                          type="button"
                          onClick={async () => {
                            const enhanced = await enhanceMessageWithAI(formData.title, "correct");
                            if (enhanced) setFormData({...formData, title: enhanced});
                          }}
                          className="text-xs text-green-600 hover:text-green-800 flex items-center space-x-1"
                        >
                          <RefreshCw className="w-3 h-3" />
                          <span>{t('ai.correct')}</span>
                        </button>
                      </div>
                    )}
                  </div>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({...formData, title: e.target.value})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder={t('create.titlePlaceholder')}
                    required
                    disabled={loading || isAtMessageLimit}
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700">
                      {t('create.messageContent')}
                    </label>
                    {formData.content && (
                      <div className="flex space-x-2">
                        <button
                          type="button"
                          onClick={async () => {
                            const enhanced = await enhanceMessageWithAI(formData.content, "improve");
                            if (enhanced) setFormData({...formData, content: enhanced});
                          }}
                          className="text-xs text-purple-600 hover:text-purple-800 flex items-center space-x-1"
                        >
                          <Wand2 className="w-3 h-3" />
                          <span>{t('ai.improve')}</span>
                        </button>
                        <button
                          type="button"
                          onClick={async () => {
                            const enhanced = await enhanceMessageWithAI(formData.content, "correct");
                            if (enhanced) setFormData({...formData, content: enhanced});
                          }}
                          className="text-xs text-green-600 hover:text-green-800 flex items-center space-x-1"
                        >
                          <RefreshCw className="w-3 h-3" />
                          <span>{t('ai.correct')}</span>
                        </button>
                      </div>
                    )}
                  </div>
                  <textarea
                    value={formData.content}
                    onChange={(e) => setFormData({...formData, content: e.target.value})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder={t('create.contentPlaceholder')}
                    rows="6"
                    required
                    disabled={loading || isAtMessageLimit}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('create.scheduledTime')}
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.scheduled_time}
                    onChange={(e) => setFormData({...formData, scheduled_time: e.target.value})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                    disabled={loading || isAtMessageLimit}
                    min={new Date().toISOString().slice(0, 16)}
                  />
                </div>

                {user?.subscription_plan !== 'free' && (
                  <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                    <div className="flex items-center space-x-2 mb-3">
                      <Repeat className="w-4 h-4 text-green-600" />
                      <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={formData.is_recurring}
                          onChange={(e) => setFormData({...formData, is_recurring: e.target.checked})}
                          className="rounded border-gray-300 text-green-600 focus:ring-green-500"
                          disabled={loading}
                        />
                        <span className="text-sm font-medium text-gray-700">{t('create.recurring')}</span>
                      </label>
                      <Crown className="w-4 h-4 text-yellow-500" />
                    </div>
                    
                    {formData.is_recurring && (
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-2">
                          {t('create.recurringInterval')}
                        </label>
                        <select
                          value={formData.recurring_pattern}
                          onChange={(e) => setFormData({...formData, recurring_pattern: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm"
                          disabled={loading}
                        >
                          <option value="">{t('create.recurringInterval')}...</option>
                          <option value="daily">{t('create.recurringDaily')}</option>
                          <option value="weekly">{t('create.recurringWeekly')}</option>
                          <option value="monthly">{t('create.recurringMonthly')}</option>
                        </select>
                      </div>
                    )}
                    
                    {user?.subscription_plan === 'free' && (
                      <p className="text-xs text-gray-500 mt-2">
                        {t('create.recurringNotice')}
                      </p>
                    )}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading || isAtMessageLimit}
                  className="w-full bg-blue-500 hover:bg-blue-600 text-white font-medium py-3 px-6 rounded-lg transition-colors disabled:opacity-50"
                >
                  {loading ? t('create.submitting') : t('create.submitButton')}
                </button>
              </form>
            )}

            {/* Bulk Messages Form */}
            {messageMode === 'bulk' && (
              <div className="space-y-6">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-3">
                    <Archive className="w-5 h-5 text-blue-600" />
                    <h3 className="font-semibold text-blue-800">Bulk-Nachrichten erstellen</h3>
                    <Crown className="w-4 h-4 text-yellow-500" />
                  </div>
                  <p className="text-sm text-blue-700 mb-3">
                    Erstellen Sie mehrere Nachrichten gleichzeitig mit automatischen Zeitintervallen.
                  </p>
                  <div className="flex items-center space-x-4">
                    <label className="text-sm font-medium text-blue-800">
                      Zeitintervall zwischen Nachrichten:
                    </label>
                    <select
                      value={timeInterval}
                      onChange={(e) => setTimeInterval(parseInt(e.target.value))}
                      className="px-3 py-1 border border-blue-300 rounded bg-white text-sm"
                    >
                      <option value={1}>1 Minute</option>
                      <option value={5}>5 Minuten</option>
                      <option value={10}>10 Minuten</option>
                      <option value={15}>15 Minuten</option>
                      <option value={30}>30 Minuten</option>
                      <option value={60}>1 Stunde</option>
                    </select>
                  </div>
                </div>

                {bulkMessages.map((message, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="font-medium text-gray-800">Nachricht {index + 1}</h4>
                      {bulkMessages.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeBulkMessage(index)}
                          className="text-red-600 hover:text-red-800 text-sm flex items-center space-x-1"
                        >
                          <Trash2 className="w-4 h-4" />
                          <span>Entfernen</span>
                        </button>
                      )}
                    </div>

                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Titel
                        </label>
                        <input
                          type="text"
                          value={message.title}
                          onChange={(e) => updateBulkMessage(index, 'title', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          placeholder="Nachrichtentitel..."
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Geplante Zeit
                        </label>
                        <input
                          type="datetime-local"
                          value={message.scheduled_time}
                          onChange={(e) => updateBulkMessage(index, 'scheduled_time', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          required
                          min={new Date().toISOString().slice(0, 16)}
                        />
                      </div>
                    </div>

                    <div className="mt-4">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Nachrichteninhalt
                      </label>
                      <textarea
                        value={message.content}
                        onChange={(e) => updateBulkMessage(index, 'content', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Nachrichteninhalt..."
                        rows="4"
                        required
                      />
                    </div>

                    <div className="mt-3 flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={message.is_recurring}
                        onChange={(e) => updateBulkMessage(index, 'is_recurring', e.target.checked)}
                        className="rounded border-gray-300 text-green-600 focus:ring-green-500"
                        disabled={loading}
                      />
                      <label className="text-sm text-gray-700">Wiederkehrende Nachricht</label>
                      <Crown className="w-3 h-3 text-yellow-500" />
                    </div>
                  </div>
                ))}

                <div className="flex items-center space-x-3">
                  <button
                    type="button"
                    onClick={addBulkMessage}
                    className="flex items-center space-x-2 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors"
                  >
                    <MessageSquare className="w-4 h-4" />
                    <span>Weitere Nachricht hinzufügen</span>
                  </button>

                  <button
                    type="button"
                    onClick={createBulkMessages}
                    disabled={loading}
                    className="flex items-center space-x-2 px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors disabled:opacity-50"
                  >
                    <Archive className="w-4 h-4" />
                    <span>{loading ? 'Wird erstellt...' : 'Bulk-Nachrichten erstellen'}</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Scheduled Messages Tab */}
        {activeTab === 'scheduled' && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-semibold text-gray-800 mb-6">
              Geplante Nachrichten ({scheduledMessages.length})
            </h2>
            {scheduledMessages.length === 0 ? (
              <div className="text-center py-8">
                <div className="text-6xl mb-4">📭</div>
                <p className="text-gray-500">Keine geplanten Nachrichten vorhanden.</p>
                <button
                  onClick={() => setActiveTab('create')}
                  className="mt-4 bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                >
                  Erste Nachricht erstellen
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {scheduledMessages.map((message) => (
                  <div
                    key={message.id}
                    className={`border rounded-lg p-4 transition-all ${
                      isMessageDueSoon(message.scheduled_time)
                        ? 'border-yellow-300 bg-yellow-50 shadow-md'
                        : 'border-gray-200 hover:shadow-md'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-800 flex items-center">
                          {isMessageDueSoon(message.scheduled_time) && (
                            <Bell className="w-4 h-4 mr-2 text-yellow-600" />
                          )}
                          {message.is_recurring && (
                            <Repeat className="w-4 h-4 mr-2 text-green-600" />
                          )}
                          {message.title}
                        </h3>
                        <div className="text-sm text-gray-600 mt-1 space-y-1">
                          <p className="flex items-center">
                            <Calendar className="w-4 h-4 mr-1" />
                            {formatDate(message.scheduled_time)}
                          </p>
                          {message.is_recurring && (
                            <p className="flex items-center text-green-600">
                              <Repeat className="w-4 h-4 mr-1" />
                              Wiederholung: {message.recurring_pattern === 'daily' ? 'Täglich' : 
                                           message.recurring_pattern === 'weekly' ? 'Wöchentlich' : 'Monatlich'}
                            </p>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={() => deleteMessage(message.id)}
                        className="text-red-500 hover:text-red-700 p-1 hover:bg-red-50 rounded"
                        title="Nachricht löschen"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                    <p className="text-gray-700 bg-gray-50 p-3 rounded-md">
                      {message.content}
                    </p>
                    {isMessageDueSoon(message.scheduled_time) && (
                      <div className="mt-3 text-sm text-yellow-700 bg-yellow-100 p-2 rounded-md">
                        ⚡ Diese Nachricht wird bald ausgeliefert!
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Delivered Messages Tab */}
        {activeTab === 'delivered' && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-semibold text-gray-800 mb-6">
              Ausgelieferte Nachrichten ({deliveredMessages.length})
            </h2>
            {deliveredMessages.length === 0 ? (
              <div className="text-center py-8">
                <div className="text-6xl mb-4">📬</div>
                <p className="text-gray-500">Noch keine Nachrichten ausgeliefert.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {deliveredMessages.map((message) => (
                  <div
                    key={message.id}
                    className="border border-green-200 bg-green-50 rounded-lg p-4"
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-800 flex items-center">
                          <CheckCircle className="w-4 h-4 mr-2 text-green-600" />
                          {message.is_recurring && (
                            <Repeat className="w-4 h-4 mr-2 text-green-600" />
                          )}
                          {message.title}
                        </h3>
                        <div className="text-sm text-gray-600 mt-1 space-y-1">
                          <p className="flex items-center">
                            <Calendar className="w-4 h-4 mr-1" />
                            Geplant: {formatDate(message.scheduled_time)}
                          </p>
                          <p className="flex items-center text-green-600">
                            <CheckCircle className="w-4 h-4 mr-1" />
                            Ausgeliefert: {formatDate(message.delivered_at)}
                          </p>
                          {message.is_recurring && (
                            <p className="flex items-center text-green-600">
                              <Repeat className="w-4 h-4 mr-1" />
                              Wiederholung: {message.recurring_pattern === 'daily' ? 'Täglich' : 
                                           message.recurring_pattern === 'weekly' ? 'Wöchentlich' : 'Monatlich'}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                    <p className="text-gray-700 bg-white p-3 rounded-md border-l-4 border-green-400">
                      {message.content}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Subscription Tab */}
        {activeTab === 'subscription' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-2xl font-semibold text-gray-800 mb-6">
                Ihr aktuelles Abo
              </h2>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-blue-800 capitalize flex items-center">
                      {user.subscription_plan === 'premium' && <Crown className="w-5 h-5 mr-2 text-yellow-500" />}
                      {user.subscription_plan === 'business' && <Building2 className="w-5 h-5 mr-2 text-purple-500" />}
                      {subscriptionPlans[user.subscription_plan]?.name || user.subscription_plan}
                    </h3>
                    <p className="text-sm text-blue-600 mt-1">
                      Nachrichten diesen Monat: {user.monthly_messages_used} 
                      {user.monthly_messages_limit === -1 ? ' (Unbegrenzt)' : ` / ${user.monthly_messages_limit}`}
                    </p>
                    <div className="mt-2">
                      <p className="text-sm text-blue-700">Ihre Features:</p>
                      <ul className="text-sm text-blue-600 mt-1 space-y-1">
                        {user.features?.map((feature, index) => (
                          <li key={index} className="flex items-center">
                            <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                            {feature}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-blue-800">
                      {subscriptionPlans[user.subscription_plan]?.price === 0 ? 'Kostenlos' : 
                       `€${subscriptionPlans[user.subscription_plan]?.price}/Monat`}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              {/* Premium Plan */}
              {user.subscription_plan !== 'premium' && (
                <div className="bg-white rounded-xl shadow-lg p-6">
                  <div className="text-center mb-6">
                    <Crown className="w-12 h-12 text-yellow-500 mx-auto mb-3" />
                    <h3 className="text-2xl font-bold text-gray-800">Premium</h3>
                    <p className="text-3xl font-bold text-yellow-600 mt-2">€9.99<span className="text-sm font-normal text-gray-500">/Monat</span></p>
                  </div>
                  <ul className="space-y-3 mb-6">
                    {subscriptionPlans.premium?.features?.map((feature, index) => (
                      <li key={index} className="flex items-center text-gray-700">
                        <CheckCircle className="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                  <button
                    onClick={() => subscribeToPlan('premium')}
                    className="w-full bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                  >
                    Auf Premium upgraden
                  </button>
                </div>
              )}

              {/* Business Plan */}
              {user.subscription_plan !== 'business' && (
                <div className="bg-white rounded-xl shadow-lg p-6">
                  <div className="text-center mb-6">
                    <Building2 className="w-12 h-12 text-purple-500 mx-auto mb-3" />
                    <h3 className="text-2xl font-bold text-gray-800">Business</h3>
                    <p className="text-3xl font-bold text-purple-600 mt-2">€29.99<span className="text-sm font-normal text-gray-500">/Monat</span></p>
                  </div>
                  <ul className="space-y-3 mb-6">
                    {subscriptionPlans.business?.features?.map((feature, index) => (
                      <li key={index} className="flex items-center text-gray-700">
                        <CheckCircle className="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                  <button
                    onClick={() => subscribeToPlan('business')}
                    className="w-full bg-purple-500 hover:bg-purple-600 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                  >
                    Auf Business upgraden
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Admin Dashboard Tab */}
        {activeTab === 'admin' && user?.role === 'admin' && (
          <div className="space-y-6">
            {/* Admin Stats Overview */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-2xl font-semibold text-gray-800 mb-6 flex items-center">
                <Shield className="w-6 h-6 mr-2 text-purple-600" />
                Admin Dashboard
              </h2>
              
              {adminStats ? (
                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-blue-600 font-medium">Benutzer Gesamt</p>
                        <p className="text-2xl font-bold text-blue-800">{adminStats.total_users}</p>
                      </div>
                      <Users className="w-8 h-8 text-blue-500" />
                    </div>
                  </div>

                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-green-600 font-medium">Monatserlös</p>
                        <p className="text-2xl font-bold text-green-800">€{adminStats.monthly_revenue.toFixed(2)}</p>
                      </div>
                      <TrendingUp className="w-8 h-8 text-green-500" />
                    </div>
                  </div>

                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-yellow-600 font-medium">Verfügbares Guthaben</p>
                        <p className="text-2xl font-bold text-yellow-800">€{adminStats.available_balance.toFixed(2)}</p>
                      </div>
                      <DollarSign className="w-8 h-8 text-yellow-500" />
                    </div>
                  </div>

                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-purple-600 font-medium">Premium Kunden</p>
                        <p className="text-2xl font-bold text-purple-800">{adminStats.premium_users + adminStats.business_users}</p>
                      </div>
                      <Crown className="w-8 h-8 text-purple-500" />
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="w-6 h-6 text-gray-400 animate-spin mr-2" />
                  <span className="text-gray-500">Lade Statistiken...</span>
                </div>
              )}

              {/* Advanced Analytics Dashboard */}
              <div className="border-t pt-8">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-semibold text-gray-800 flex items-center">
                    <BarChart3 className="w-6 h-6 mr-2 text-blue-600" />
                    Erweiterte Analytik
                  </h3>
                  <div className="flex items-center space-x-4">
                    <button
                      onClick={() => exportAnalytics('json')}
                      className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded-lg transition-colors flex items-center"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      JSON Export
                    </button>
                    <button
                      onClick={() => fetchAdvancedAnalytics()}
                      className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white text-sm rounded-lg transition-colors flex items-center"
                      disabled={analyticsLoading}
                    >
                      <RefreshCw className={`w-4 h-4 mr-2 ${analyticsLoading ? 'animate-spin' : ''}`} />
                      Aktualisieren
                    </button>
                  </div>
                </div>

                {analyticsLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <RefreshCw className="w-8 h-8 text-blue-500 animate-spin mr-3" />
                    <span className="text-gray-600 text-lg">Lade erweiterte Analytik...</span>
                  </div>
                ) : advancedAnalytics ? (
                  <>
                    {/* Analytics Navigation Tabs */}
                    <div className="flex border-b border-gray-200 mb-6">
                      {[
                        { id: 'overview', label: 'Übersicht', icon: Eye },
                        { id: 'users', label: 'Benutzer', icon: Users },
                        { id: 'messages', label: 'Nachrichten', icon: MessageSquare },
                        { id: 'revenue', label: 'Umsatz', icon: DollarSign },
                        { id: 'ai', label: 'KI-Nutzung', icon: Brain },
                        { id: 'contacts', label: 'Kontakte & Email', icon: Send }
                      ].map((tab) => (
                        <button
                          key={tab.id}
                          onClick={() => setSelectedAnalyticsTab(tab.id)}
                          className={`flex items-center space-x-2 px-6 py-3 border-b-2 font-medium text-sm transition-colors ${
                            selectedAnalyticsTab === tab.id
                              ? 'border-blue-500 text-blue-600'
                              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                          }`}
                        >
                          <tab.icon className="w-4 h-4" />
                          <span>{tab.label}</span>
                        </button>
                      ))}
                    </div>

                    {/* Analytics Content */}
                    {selectedAnalyticsTab === 'overview' && (
                      <div className="space-y-6">
                        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="text-sm text-blue-600 font-medium">Konversionsrate</p>
                                <p className="text-2xl font-bold text-blue-800">{advancedAnalytics.user_analytics.subscription_conversion_rate}%</p>
                              </div>
                              <Target className="w-8 h-8 text-blue-500" />
                            </div>
                          </div>

                          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="text-sm text-green-600 font-medium">Nutzerretention</p>
                                <p className="text-2xl font-bold text-green-800">{advancedAnalytics.user_analytics.user_retention_rate}%</p>
                              </div>
                              <Activity className="w-8 h-8 text-green-500" />
                            </div>
                          </div>

                          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="text-sm text-purple-600 font-medium">Durchschn. Umsatz/User</p>
                                <p className="text-2xl font-bold text-purple-800">€{advancedAnalytics.revenue_analytics.arpu}</p>
                              </div>
                              <TrendingUp className="w-8 h-8 text-purple-500" />
                            </div>
                          </div>

                          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="text-sm text-orange-600 font-medium">KI-Adoption</p>
                                <p className="text-2xl font-bold text-orange-800">{advancedAnalytics.ai_analytics.ai_adoption_rate}%</p>
                              </div>
                              <Zap className="w-8 h-8 text-orange-500" />
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {selectedAnalyticsTab === 'users' && (
                      <div className="space-y-6">
                        <div className="grid md:grid-cols-2 gap-6">
                          {/* Registration Trends */}
                          <div className="bg-white border border-gray-200 rounded-lg p-6">
                            <h4 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                              <LineChart className="w-5 h-5 mr-2 text-blue-600" />
                              Registrierungstrends (30 Tage)
                            </h4>
                            <div className="space-y-2">
                              {advancedAnalytics.user_analytics.registration_trends.slice(-5).map((trend, index) => (
                                <div key={index} className="flex justify-between items-center py-2 border-b border-gray-100">
                                  <span className="text-gray-600">{trend._id}</span>
                                  <span className="font-medium text-blue-600">{trend.count} Registrierungen</span>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Top Referrers */}
                          <div className="bg-white border border-gray-200 rounded-lg p-6">
                            <h4 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                              <Users className="w-5 h-5 mr-2 text-green-600" />
                              Top Einladende
                            </h4>
                            <div className="space-y-3">
                              {advancedAnalytics.user_analytics.top_referrers.slice(0, 5).map((referrer, index) => (
                                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                  <div>
                                    <p className="font-medium text-gray-800">{referrer.referrer_name}</p>
                                    <p className="text-sm text-gray-500">{referrer.referrer_email}</p>
                                  </div>
                                  <div className="text-right">
                                    <p className="font-bold text-green-600">{referrer.referrals}</p>
                                    <p className="text-xs text-gray-500">Einladungen</p>
                                  </div>
                                </div>
                              ))}
                              {advancedAnalytics.user_analytics.top_referrers.length === 0 && (
                                <p className="text-gray-500 text-center py-4">Noch keine Einladungen vorhanden</p>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Activity Heatmap */}
                        <div className="bg-white border border-gray-200 rounded-lg p-6">
                          <h4 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                            <Activity className="w-5 h-5 mr-2 text-purple-600" />
                            Nutzeraktivität nach Tageszeit
                          </h4>
                          <div className="grid grid-cols-12 gap-2">
                            {Array.from({ length: 24 }, (_, hour) => {
                              const hourData = advancedAnalytics.user_analytics.user_activity_heatmap.find(h => h._id === hour);
                              const count = hourData ? hourData.count : 0;
                              const maxCount = Math.max(...advancedAnalytics.user_analytics.user_activity_heatmap.map(h => h.count));
                              const intensity = maxCount > 0 ? (count / maxCount) : 0;
                              
                              return (
                                <div
                                  key={hour}
                                  className="text-center p-2 rounded"
                                  style={{
                                    backgroundColor: `rgba(59, 130, 246, ${0.1 + intensity * 0.8})`
                                  }}
                                  title={`${hour}:00 - ${count} Aktivitäten`}
                                >
                                  <div className="text-xs font-medium text-gray-700">{hour}</div>
                                  <div className="text-xs text-gray-600">{count}</div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                    )}

                    {selectedAnalyticsTab === 'messages' && (
                      <div className="space-y-6">
                        <div className="grid md:grid-cols-2 gap-6">
                          {/* Message Creation Patterns */}
                          <div className="bg-white border border-gray-200 rounded-lg p-6">
                            <h4 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                              <LineChart className="w-5 h-5 mr-2 text-blue-600" />
                              Nachrichtenerstellung (30 Tage)
                            </h4>
                            <div className="space-y-2">
                              {advancedAnalytics.message_analytics.creation_patterns.slice(-5).map((pattern, index) => (
                                <div key={index} className="flex justify-between items-center py-2 border-b border-gray-100">
                                  <span className="text-gray-600">{pattern._id}</span>
                                  <span className="font-medium text-blue-600">{pattern.count} Nachrichten</span>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Message Type Distribution */}
                          <div className="bg-white border border-gray-200 rounded-lg p-6">
                            <h4 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                              <PieChart className="w-5 h-5 mr-2 text-green-600" />
                              Nachrichtentypen
                            </h4>
                            <div className="space-y-3">
                              {advancedAnalytics.message_analytics.message_type_distribution.map((type, index) => (
                                <div key={index} className="flex items-center justify-between">
                                  <div className="flex items-center">
                                    <div className={`w-3 h-3 rounded-full mr-3 ${index === 0 ? 'bg-blue-500' : 'bg-green-500'}`}></div>
                                    <span className="text-gray-700">{type.type}</span>
                                  </div>
                                  <span className="font-medium">{type.count}</span>
                                </div>
                              ))}
                            </div>
                            <div className="mt-4 pt-4 border-t border-gray-200">
                              <div className="text-sm text-gray-600">
                                <p>Erfolgsrate der Zustellung: <span className="font-medium text-green-600">{advancedAnalytics.message_analytics.delivery_success_rate}%</span></p>
                                <p>Wiederkehrende Nachrichten: <span className="font-medium text-purple-600">{advancedAnalytics.message_analytics.recurring_vs_oneshot.recurring_percentage}%</span></p>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Popular Scheduling Times */}
                        <div className="bg-white border border-gray-200 rounded-lg p-6">
                          <h4 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                            <Clock className="w-5 h-5 mr-2 text-purple-600" />
                            Beliebte Planungszeiten
                          </h4>
                          <div className="grid grid-cols-12 gap-2">
                            {Array.from({ length: 24 }, (_, hour) => {
                              const hourData = advancedAnalytics.message_analytics.popular_times.find(h => h._id === hour);
                              const count = hourData ? hourData.count : 0;
                              const maxCount = Math.max(...advancedAnalytics.message_analytics.popular_times.map(h => h.count));
                              const intensity = maxCount > 0 ? (count / maxCount) : 0;
                              
                              return (
                                <div
                                  key={hour}
                                  className="text-center p-2 rounded"
                                  style={{
                                    backgroundColor: `rgba(147, 51, 234, ${0.1 + intensity * 0.8})`
                                  }}
                                  title={`${hour}:00 - ${count} geplante Nachrichten`}
                                >
                                  <div className="text-xs font-medium text-gray-700">{hour}</div>
                                  <div className="text-xs text-gray-600">{count}</div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                    )}

                    {selectedAnalyticsTab === 'revenue' && (
                      <div className="space-y-6">
                        <div className="grid md:grid-cols-3 gap-4">
                          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                            <div className="text-center">
                              <p className="text-sm text-green-600 font-medium">Durchschn. Umsatz/User</p>
                              <p className="text-2xl font-bold text-green-800">€{advancedAnalytics.revenue_analytics.arpu}</p>
                            </div>
                          </div>

                          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                            <div className="text-center">
                              <p className="text-sm text-red-600 font-medium">Abwanderungsrate</p>
                              <p className="text-2xl font-bold text-red-800">{advancedAnalytics.revenue_analytics.churn_rate}%</p>
                            </div>
                          </div>

                          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                            <div className="text-center">
                              <p className="text-sm text-blue-600 font-medium">Wachstumsrate</p>
                              <p className="text-2xl font-bold text-blue-800">{advancedAnalytics.revenue_analytics.subscription_growth_rate}%</p>
                            </div>
                          </div>
                        </div>

                        <div className="grid md:grid-cols-2 gap-6">
                          {/* MRR Trend */}
                          <div className="bg-white border border-gray-200 rounded-lg p-6">
                            <h4 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                              <TrendingUp className="w-5 h-5 mr-2 text-green-600" />
                              Monatliche Umsätze (MRR)
                            </h4>
                            <div className="space-y-2">
                              {advancedAnalytics.revenue_analytics.mrr_trend.slice(-6).map((trend, index) => (
                                <div key={index} className="flex justify-between items-center py-2 border-b border-gray-100">
                                  <span className="text-gray-600">{trend._id}</span>
                                  <span className="font-medium text-green-600">€{trend.revenue?.toFixed(2)}</span>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Revenue by Plan */}
                          <div className="bg-white border border-gray-200 rounded-lg p-6">
                            <h4 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                              <PieChart className="w-5 h-5 mr-2 text-purple-600" />
                              Umsatz nach Plan
                            </h4>
                            <div className="space-y-3">
                              {advancedAnalytics.revenue_analytics.revenue_by_plan.map((plan, index) => (
                                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                  <div>
                                    <p className="font-medium text-gray-800 capitalize">{plan._id}</p>
                                    <p className="text-sm text-gray-500">{plan.subscribers} Abonnenten</p>
                                  </div>
                                  <div className="text-right">
                                    <p className="font-bold text-green-600">€{plan.revenue?.toFixed(2)}</p>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {selectedAnalyticsTab === 'ai' && (
                      <div className="space-y-6">
                        <div className="grid md:grid-cols-2 gap-4">
                          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                            <div className="text-center">
                              <p className="text-sm text-purple-600 font-medium">KI-Erfolgsrate</p>
                              <p className="text-2xl font-bold text-purple-800">{advancedAnalytics.ai_analytics.generation_success_rate}%</p>
                            </div>
                          </div>

                          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                            <div className="text-center">
                              <p className="text-sm text-blue-600 font-medium">KI-Adoptionsrate</p>
                              <p className="text-2xl font-bold text-blue-800">{advancedAnalytics.ai_analytics.ai_adoption_rate}%</p>
                            </div>
                          </div>
                        </div>

                        <div className="grid md:grid-cols-2 gap-6">
                          {/* Feature Usage */}
                          <div className="bg-white border border-gray-200 rounded-lg p-6">
                            <h4 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                              <Brain className="w-5 h-5 mr-2 text-purple-600" />
                              KI-Feature Nutzung
                            </h4>
                            <div className="space-y-3">
                              {advancedAnalytics.ai_analytics.feature_usage.map((feature, index) => (
                                <div key={index} className="space-y-2">
                                  <div className="flex justify-between">
                                    <span className="text-gray-700">{feature.feature}</span>
                                    <span className="font-medium">{feature.percentage}%</span>
                                  </div>
                                  <div className="w-full bg-gray-200 rounded-full h-2">
                                    <div 
                                      className="bg-purple-600 h-2 rounded-full" 
                                      style={{ width: `${feature.percentage}%` }}
                                    ></div>
                                  </div>
                                  <div className="text-xs text-gray-500">{feature.usage_count} Verwendungen</div>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Popular Prompts */}
                          <div className="bg-white border border-gray-200 rounded-lg p-6">
                            <h4 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                              <Lightbulb className="w-5 h-5 mr-2 text-yellow-600" />
                              Beliebte Prompts
                            </h4>
                            <div className="space-y-3">
                              {advancedAnalytics.ai_analytics.popular_prompts.map((prompt, index) => (
                                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                  <span className="text-gray-700">{prompt.prompt_type}</span>
                                  <span className="font-medium text-yellow-600">{prompt.usage_count}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>

                        {/* Enhancement Types */}
                        <div className="bg-white border border-gray-200 rounded-lg p-6">
                          <h4 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                            <Wand2 className="w-5 h-5 mr-2 text-green-600" />
                            Text-Verbesserungen
                          </h4>
                          <div className="grid md:grid-cols-4 gap-4">
                            {advancedAnalytics.ai_analytics.enhancement_types.map((enhancement, index) => (
                              <div key={index} className="text-center p-4 bg-gray-50 rounded-lg">
                                <p className="text-lg font-bold text-gray-800">{enhancement.count}</p>
                                <p className="text-sm text-gray-600">{enhancement.type}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}

                    {selectedAnalyticsTab === 'contacts' && (
                      <div className="space-y-6">
                        {contactManagementLoading ? (
                          <div className="flex items-center justify-center py-12">
                            <RefreshCw className="w-8 h-8 text-blue-500 animate-spin mr-3" />
                            <span className="text-gray-600 text-lg">Lade Contact & Email Daten...</span>
                          </div>
                        ) : (
                          <>
                            {/* Contact & Email Overview Cards */}
                            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <p className="text-sm text-blue-600 font-medium">Alle Kontakte</p>
                                    <p className="text-2xl font-bold text-blue-800">
                                      {contactsOverview?.contacts_overview?.total_contacts || 0}
                                    </p>
                                  </div>
                                  <Users className="w-8 h-8 text-blue-500" />
                                </div>
                              </div>

                              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <p className="text-sm text-green-600 font-medium">Email Zustellungen</p>
                                    <p className="text-2xl font-bold text-green-800">
                                      {emailDeliveriesOverview?.delivery_overview?.total_deliveries || 0}
                                    </p>
                                  </div>
                                  <Send className="w-8 h-8 text-green-500" />
                                </div>
                              </div>

                              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <p className="text-sm text-purple-600 font-medium">Erfolgsrate Email</p>
                                    <p className="text-2xl font-bold text-purple-800">
                                      {emailDeliveriesOverview?.delivery_overview?.success_rate || 0}%
                                    </p>
                                  </div>
                                  <CheckCircle className="w-8 h-8 text-purple-500" />
                                </div>
                              </div>

                              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <p className="text-sm text-red-600 font-medium">Fehler (24h)</p>
                                    <p className="text-2xl font-bold text-red-800">
                                      {emailDeliveriesOverview?.delivery_overview?.recent_failed_24h || 0}
                                    </p>
                                  </div>
                                  <Bell className="w-8 h-8 text-red-500" />
                                </div>
                              </div>
                            </div>

                            {/* Contact & Email Management Tabs */}
                            <div className="flex border-b border-gray-200 mb-6">
                              {[
                                { id: 'overview', label: 'Übersicht', icon: Eye },
                                { id: 'contacts', label: 'Alle Kontakte', icon: Users },
                                { id: 'deliveries', label: 'Email Zustellungen', icon: Send },
                                { id: 'errors', label: 'Fehler & Probleme', icon: Bell }
                              ].map((tab) => (
                                <button
                                  key={tab.id}
                                  onClick={() => setSelectedContactTab(tab.id)}
                                  className={`flex items-center space-x-2 px-6 py-3 border-b-2 font-medium text-sm transition-colors ${
                                    selectedContactTab === tab.id
                                      ? 'border-blue-500 text-blue-600'
                                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                  }`}
                                >
                                  <tab.icon className="w-4 h-4" />
                                  <span>{tab.label}</span>
                                </button>
                              ))}
                            </div>

                            {/* Contact Management Tab Content */}
                            {selectedContactTab === 'overview' && (
                              <div className="grid md:grid-cols-2 gap-6">
                                {/* Contact Types Breakdown */}
                                <div className="bg-white border border-gray-200 rounded-lg p-6">
                                  <h4 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                                    <Users className="w-5 h-5 mr-2 text-blue-600" />
                                    Kontakt-Typen
                                  </h4>
                                  <div className="space-y-3">
                                    {contactsOverview?.contacts_overview?.contact_types?.map((type, index) => (
                                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                        <span className="text-gray-700 capitalize">{type._id}</span>
                                        <span className="font-medium text-blue-600">{type.count}</span>
                                      </div>
                                    ))}
                                  </div>
                                </div>

                                {/* Email Delivery Status */}
                                <div className="bg-white border border-gray-200 rounded-lg p-6">
                                  <h4 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                                    <Send className="w-5 h-5 mr-2 text-green-600" />
                                    Email-Zustellstatus
                                  </h4>
                                  <div className="space-y-3">
                                    {emailDeliveriesOverview?.delivery_statuses?.map((status, index) => (
                                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                        <span className={`text-gray-700 capitalize ${
                                          status._id === 'delivered' ? 'text-green-700' :
                                          status._id === 'failed' ? 'text-red-700' :
                                          status._id === 'sent' ? 'text-blue-700' : ''
                                        }`}>
                                          {status._id}
                                        </span>
                                        <span className="font-medium">{status.count}</span>
                                      </div>
                                    ))}
                                  </div>
                                </div>

                                {/* Top Users by Contacts */}
                                <div className="bg-white border border-gray-200 rounded-lg p-6">
                                  <h4 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                                    <Crown className="w-5 h-5 mr-2 text-yellow-600" />
                                    Top Nutzer (Kontakte)
                                  </h4>
                                  <div className="space-y-3">
                                    {contactsOverview?.contacts_overview?.top_users_by_contacts?.slice(0, 5).map((userStat, index) => (
                                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                        <div>
                                          <p className="font-medium text-gray-800">{userStat.user_name || 'Unknown'}</p>
                                          <p className="text-sm text-gray-500">{userStat.user_email || ''}</p>
                                        </div>
                                        <span className="font-medium text-yellow-600">{userStat.contact_count} Kontakte</span>
                                      </div>
                                    ))}
                                  </div>
                                </div>

                                {/* Top Email Senders */}
                                <div className="bg-white border border-gray-200 rounded-lg p-6">
                                  <h4 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                                    <Send className="w-5 h-5 mr-2 text-purple-600" />
                                    Top Email-Absender
                                  </h4>
                                  <div className="space-y-3">
                                    {emailDeliveriesOverview?.top_senders?.slice(0, 5).map((sender, index) => (
                                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                        <div>
                                          <p className="font-medium text-gray-800">{sender.user_name || 'Unknown'}</p>
                                          <p className="text-sm text-gray-500">{sender.user_email || ''}</p>
                                        </div>
                                        <span className="font-medium text-purple-600">{sender.email_count} Emails</span>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              </div>
                            )}

                            {selectedContactTab === 'contacts' && (
                              <div className="space-y-6">
                                {/* Search and Filter Controls */}
                                <div className="bg-white border border-gray-200 rounded-lg p-4">
                                  <div className="flex items-center space-x-4">
                                    <div className="flex-1">
                                      <input
                                        type="text"
                                        value={contactSearchTerm}
                                        onChange={(e) => setContactSearchTerm(e.target.value)}
                                        onKeyPress={(e) => e.key === 'Enter' && searchContacts(contactSearchTerm, contactTypeFilter)}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                        placeholder="Suche nach Name, Email oder Unternehmen..."
                                      />
                                    </div>
                                    <select
                                      value={contactTypeFilter}
                                      onChange={(e) => setContactTypeFilter(e.target.value)}
                                      className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                    >
                                      <option value="">Alle Typen</option>
                                      <option value="personal">Personal</option>
                                      <option value="business">Business</option>
                                      <option value="family">Family</option>
                                    </select>
                                    <button
                                      onClick={() => searchContacts(contactSearchTerm, contactTypeFilter)}
                                      className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors flex items-center"
                                    >
                                      <Filter className="w-4 h-4 mr-2" />
                                      Suchen
                                    </button>
                                  </div>
                                </div>

                                {/* All Contacts List */}
                                <div className="bg-white border border-gray-200 rounded-lg p-6">
                                  <h4 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                                    <Users className="w-5 h-5 mr-2 text-blue-600" />
                                    Alle Kontakte ({allContacts.length})
                                  </h4>
                                  <div className="space-y-3">
                                    {allContacts.map((contact, index) => (
                                      <div key={index} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
                                        <div className="flex-1">
                                          <div className="flex items-center space-x-4">
                                            <div>
                                              <p className="font-medium text-gray-800">{contact.name}</p>
                                              <p className="text-sm text-gray-600">{contact.email}</p>
                                              {contact.company && (
                                                <p className="text-sm text-blue-600">{contact.company}</p>
                                              )}
                                            </div>
                                          </div>
                                        </div>
                                        <div className="text-right">
                                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                                            contact.contact_type === 'business' ? 'bg-blue-100 text-blue-800' :
                                            contact.contact_type === 'personal' ? 'bg-green-100 text-green-800' :
                                            'bg-gray-100 text-gray-800'
                                          }`}>
                                            {contact.contact_type}
                                          </span>
                                          <p className="text-xs text-gray-500 mt-1">
                                            von: {contact.owner_name || 'Unknown'}
                                          </p>
                                        </div>
                                      </div>
                                    ))}
                                    {allContacts.length === 0 && (
                                      <div className="text-center py-8">
                                        <Users className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                                        <p className="text-gray-500">Keine Kontakte gefunden</p>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </div>
                            )}

                            {selectedContactTab === 'deliveries' && (
                              <div className="space-y-6">
                                {/* Delivery Filter Controls */}
                                <div className="bg-white border border-gray-200 rounded-lg p-4">
                                  <div className="flex items-center space-x-4">
                                    <select
                                      value={deliveryStatusFilter}
                                      onChange={(e) => setDeliveryStatusFilter(e.target.value)}
                                      className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                    >
                                      <option value="">Alle Status</option>
                                      <option value="pending">Ausstehend</option>
                                      <option value="sent">Gesendet</option>
                                      <option value="delivered">Zugestellt</option>
                                      <option value="failed">Fehlgeschlagen</option>
                                      <option value="opened">Geöffnet</option>
                                    </select>
                                    <button
                                      onClick={() => filterDeliveries(deliveryStatusFilter)}
                                      className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors flex items-center"
                                    >
                                      <Filter className="w-4 h-4 mr-2" />
                                      Filtern
                                    </button>
                                  </div>
                                </div>

                                {/* Recent Deliveries List */}
                                <div className="bg-white border border-gray-200 rounded-lg p-6">
                                  <h4 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                                    <Send className="w-5 h-5 mr-2 text-green-600" />
                                    Aktuelle Email-Zustellungen ({recentDeliveries.length})
                                  </h4>
                                  <div className="space-y-3">
                                    {recentDeliveries.map((delivery, index) => (
                                      <div key={index} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
                                        <div className="flex-1">
                                          <p className="font-medium text-gray-800">{delivery.subject}</p>
                                          <p className="text-sm text-gray-600">An: {delivery.recipient_email}</p>
                                          <p className="text-sm text-gray-500">
                                            Von: {delivery.sender_name || 'Unknown'} ({delivery.sender_email})
                                          </p>
                                          {delivery.message_title && (
                                            <p className="text-sm text-blue-600">Nachricht: {delivery.message_title}</p>
                                          )}
                                        </div>
                                        <div className="text-right">
                                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                                            delivery.delivery_status === 'delivered' ? 'bg-green-100 text-green-800' :
                                            delivery.delivery_status === 'sent' ? 'bg-blue-100 text-blue-800' :
                                            delivery.delivery_status === 'failed' ? 'bg-red-100 text-red-800' :
                                            delivery.delivery_status === 'opened' ? 'bg-purple-100 text-purple-800' :
                                            'bg-gray-100 text-gray-800'
                                          }`}>
                                            {delivery.delivery_status}
                                          </span>
                                          {delivery.sent_at && (
                                            <p className="text-xs text-gray-500 mt-1">
                                              {new Date(delivery.sent_at).toLocaleString('de-DE')}
                                            </p>
                                          )}
                                        </div>
                                      </div>
                                    ))}
                                    {recentDeliveries.length === 0 && (
                                      <div className="text-center py-8">
                                        <Send className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                                        <p className="text-gray-500">Keine Email-Zustellungen gefunden</p>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </div>
                            )}

                            {selectedContactTab === 'errors' && (
                              <div className="space-y-6">
                                {/* Recent Email Errors */}
                                <div className="bg-white border border-gray-200 rounded-lg p-6">
                                  <h4 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                                    <Bell className="w-5 h-5 mr-2 text-red-600" />
                                    Aktuelle Email-Fehler
                                  </h4>
                                  <div className="space-y-3">
                                    {emailDeliveriesOverview?.recent_errors?.map((error, index) => (
                                      <div key={index} className="p-4 border border-red-200 rounded-lg bg-red-50">
                                        <div className="flex items-start justify-between">
                                          <div>
                                            <p className="font-medium text-red-800">Email-Fehler</p>
                                            <p className="text-sm text-red-700">An: {error.recipient_email}</p>
                                            <p className="text-sm text-red-600 mt-2">{error.error_message}</p>
                                          </div>
                                          <div className="text-right text-xs text-red-500">
                                            {error.sent_at && new Date(error.sent_at).toLocaleString('de-DE')}
                                          </div>
                                        </div>
                                      </div>
                                    ))}
                                    {(!emailDeliveriesOverview?.recent_errors || emailDeliveriesOverview.recent_errors.length === 0) && (
                                      <div className="text-center py-8">
                                        <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
                                        <p className="text-gray-500">Keine aktuellen Fehler - Alles läuft gut! ✅</p>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-center py-12">
                    <BarChart3 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500 text-lg">Erweiterte Analytik nicht verfügbar</p>
                    <p className="text-gray-400">Laden Sie die Daten neu oder überprüfen Sie Ihre Berechtigung.</p>
                  </div>
                )}
              </div>

              {/* Bank Payout Section */}
              <div className="border-t pt-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                  <DollarSign className="w-5 h-5 mr-2 text-green-600" />
                  Bank-Auszahlung
                </h3>
                
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                  <div className="grid md:grid-cols-3 gap-4 text-center">
                    <div>
                      <p className="text-sm text-green-700">Gesamteinnahmen</p>
                      <p className="text-xl font-bold text-green-800">
                        €{adminStats?.total_revenue.toFixed(2) || '0.00'}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-green-700">Verfügbar für Auszahlung</p>
                      <p className="text-xl font-bold text-green-800">
                        €{adminStats?.available_balance.toFixed(2) || '0.00'}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-orange-700">Ausstehende Auszahlungen</p>
                      <p className="text-xl font-bold text-orange-800">
                        €{adminStats?.pending_payouts.toFixed(2) || '0.00'}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <input
                    type="number"
                    value={payoutAmount}
                    onChange={(e) => setPayoutAmount(e.target.value)}
                    placeholder="Auszahlungsbetrag in €"
                    className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    min="10"
                    max={adminStats?.available_balance || 0}
                    step="0.01"
                  />
                  <button
                    onClick={requestPayout}
                    disabled={payoutLoading || !payoutAmount || parseFloat(payoutAmount) <= 0}
                    className="px-6 py-3 bg-green-500 hover:bg-green-600 text-white font-medium rounded-lg transition-colors disabled:opacity-50 flex items-center"
                  >
                    {payoutLoading ? (
                      <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                    ) : (
                      <Download className="w-4 h-4 mr-2" />
                    )}
                    {payoutLoading ? 'Wird bearbeitet...' : 'Auszahlung anfordern'}
                  </button>
                </div>

                <p className="text-xs text-gray-500 mt-2">
                  Mindestbetrag: €10.00 • Bearbeitungszeit: 1-3 Werktage
                </p>
              </div>
            </div>

            {/* Recent Transactions */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <FileText className="w-5 h-5 mr-2 text-blue-600" />
                Neueste Transaktionen
              </h3>
              
              {adminData.transactions.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="text-left p-3 font-medium text-gray-700">Datum</th>
                        <th className="text-left p-3 font-medium text-gray-700">Kunde</th>
                        <th className="text-left p-3 font-medium text-gray-700">Plan</th>
                        <th className="text-left p-3 font-medium text-gray-700">Betrag</th>
                        <th className="text-left p-3 font-medium text-gray-700">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {adminData.transactions.slice(0, 10).map((transaction, index) => (
                        <tr key={index} className="border-t border-gray-200">
                          <td className="p-3">
                            {new Date(transaction.created_at).toLocaleDateString('de-DE')}
                          </td>
                          <td className="p-3">
                            <div>
                              <div className="font-medium">{transaction.user_name}</div>
                              <div className="text-gray-500 text-xs">{transaction.user_email}</div>
                            </div>
                          </td>
                          <td className="p-3">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              transaction.subscription_plan === 'premium' 
                                ? 'bg-yellow-100 text-yellow-800' 
                                : 'bg-purple-100 text-purple-800'
                            }`}>
                              {transaction.subscription_plan}
                            </span>
                          </td>
                          <td className="p-3 font-medium">€{transaction.amount.toFixed(2)}</td>
                          <td className="p-3">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              transaction.payment_status === 'completed' 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-orange-100 text-orange-800'
                            }`}>
                              {transaction.payment_status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-8">
                  <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-500">Keine Transaktionen vorhanden</p>
                </div>
              )}
            </div>

            {/* Payout History */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <Download className="w-5 h-5 mr-2 text-green-600" />
                Auszahlungsverlauf
              </h3>
              
              {adminData.payouts.length > 0 ? (
                <div className="space-y-3">
                  {adminData.payouts.map((payout, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-center">
                        <div>
                          <div className="font-medium">€{payout.amount.toFixed(2)}</div>
                          <div className="text-sm text-gray-500">
                            {new Date(payout.requested_at).toLocaleDateString('de-DE')} • {payout.description}
                          </div>
                        </div>
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                          payout.status === 'completed' 
                            ? 'bg-green-100 text-green-800' 
                            : payout.status === 'pending'
                            ? 'bg-orange-100 text-orange-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {payout.status === 'completed' ? 'Abgeschlossen' : 
                           payout.status === 'pending' ? 'Ausstehend' : 'Fehlgeschlagen'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Download className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-500">Keine Auszahlungen vorhanden</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Referral Tab */}
        {activeTab === 'referral' && (
          <div className="space-y-6">
            {/* Referral Overview */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-2xl font-semibold text-gray-800 mb-6 flex items-center">
                <Share className="w-6 h-6 mr-2 text-green-600" />
                Freunde einladen & Belohnungen erhalten
              </h2>

              {referralData ? (
                <>
                  {/* Stats Cards */}
                  <div className="grid md:grid-cols-3 gap-4 mb-8">
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-green-600 font-medium">Eingeladene Freunde</p>
                          <p className="text-2xl font-bold text-green-800">{referralData.total_referrals}</p>
                        </div>
                        <Users className="w-8 h-8 text-green-500" />
                      </div>
                    </div>

                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-blue-600 font-medium">Bonus-Nachrichten</p>
                          <p className="text-2xl font-bold text-blue-800">{referralData.bonus_messages_earned}</p>
                        </div>
                        <Gift className="w-8 h-8 text-blue-500" />
                      </div>
                    </div>

                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-purple-600 font-medium">Ihr Referral-Code</p>
                          <p className="text-2xl font-bold text-purple-800">{referralData.referral_code}</p>
                        </div>
                        <Crown className="w-8 h-8 text-purple-500" />
                      </div>
                    </div>
                  </div>

                  {/* Referral Link Section */}
                  <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-6 mb-8">
                    <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                      <Share className="w-5 h-5 mr-2 text-green-600" />
                      Ihr persönlicher Einladungslink
                    </h3>
                    
                    <div className="bg-white border border-gray-300 rounded-lg p-3 mb-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1 mr-4">
                          <p className="text-sm font-medium text-gray-800 truncate">
                            {referralData.referral_link}
                          </p>
                        </div>
                        <button
                          onClick={copyReferralLink}
                          className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                            copySuccess 
                              ? 'bg-green-500 text-white' 
                              : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                          }`}
                        >
                          {copySuccess ? (
                            <>
                              <CheckCircle className="w-4 h-4" />
                              <span>Kopiert!</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-4 h-4" />
                              <span>Kopieren</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-4 text-sm text-gray-700">
                      <div className="flex items-center space-x-2">
                        <Gift className="w-4 h-4 text-green-600" />
                        <span>Sie erhalten 5 Bonus-Nachrichten pro Freund</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Users className="w-4 h-4 text-blue-600" />
                        <span>Ihre Freunde erhalten ebenfalls 5 Bonus-Nachrichten</span>
                      </div>
                    </div>
                  </div>

                  {/* How it works */}
                  <div className="bg-gray-50 rounded-lg p-6 mb-8">
                    <h3 className="text-lg font-semibold text-gray-800 mb-4">
                      🎉 So funktioniert's:
                    </h3>
                    <div className="space-y-3 text-gray-700">
                      <div className="flex items-start space-x-3">
                        <span className="bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">1</span>
                        <div>
                          <p className="font-medium">Link teilen</p>
                          <p className="text-sm text-gray-600">Teilen Sie Ihren persönlichen Einladungslink mit Freunden und Familie</p>
                        </div>
                      </div>
                      <div className="flex items-start space-x-3">
                        <span className="bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">2</span>
                        <div>
                          <p className="font-medium">Freund registriert sich</p>
                          <p className="text-sm text-gray-600">Ihr Freund registriert sich über Ihren Link und erhält sofort 5 Bonus-Nachrichten</p>
                        </div>
                      </div>
                      <div className="flex items-start space-x-3">
                        <span className="bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">3</span>
                        <div>
                          <p className="font-medium">Belohnung erhalten</p>
                          <p className="text-sm text-gray-600">Sie erhalten ebenfalls 5 Bonus-Nachrichten - eine Win-Win-Situation!</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Referred Users List */}
                  {referralData.referred_users && referralData.referred_users.length > 0 && (
                    <div className="bg-white border border-gray-200 rounded-lg p-6">
                      <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                        <Users className="w-5 h-5 mr-2 text-blue-600" />
                        Ihre eingeladenen Freunde ({referralData.referred_users.length})
                      </h3>
                      
                      <div className="space-y-3">
                        {referralData.referred_users.map((referredUser, index) => (
                          <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                            <div>
                              <p className="font-medium text-gray-800">{referredUser.name}</p>
                              <p className="text-sm text-gray-600">{referredUser.email}</p>
                            </div>
                            <div className="text-right">
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                referredUser.subscription_plan === 'premium' 
                                  ? 'bg-yellow-100 text-yellow-800' 
                                  : referredUser.subscription_plan === 'business'
                                  ? 'bg-purple-100 text-purple-800'
                                  : 'bg-gray-100 text-gray-800'
                              }`}>
                                {referredUser.subscription_plan}
                              </span>
                              <p className="text-xs text-gray-500 mt-1">
                                {new Date(referredUser.created_at).toLocaleDateString('de-DE')}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="w-6 h-6 text-gray-400 animate-spin mr-2" />
                  <span className="text-gray-500">Lade Referral-Daten...</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Subscription Success Page
const SubscriptionSuccess = () => {
  const { refreshUser } = useAuth();
  const [status, setStatus] = useState('checking');
  
  useEffect(() => {
    const checkPaymentStatus = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const sessionId = urlParams.get('session_id');
      
      if (sessionId) {
        try {
          const response = await axios.get(`${API}/subscriptions/status/${sessionId}`);
          if (response.data.payment_status === 'paid') {
            setStatus('success');
            await refreshUser(); // Refresh user data
          } else {
            setStatus('pending');
            // Poll for status updates
            setTimeout(checkPaymentStatus, 3000);
          }
        } catch (error) {
          console.error('Error checking payment status:', error);
          setStatus('error');
        }
      } else {
        setStatus('error');
      }
    };

    checkPaymentStatus();
  }, [refreshUser]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full text-center">
        {status === 'checking' && (
          <>
            <div className="text-6xl mb-4">⏳</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Zahlung wird überprüft...</h2>
            <p className="text-gray-600">Bitte warten Sie einen Moment.</p>
          </>
        )}
        
        {status === 'success' && (
          <>
            <div className="text-6xl mb-4">🎉</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Willkommen im Premium-Club!</h2>
            <p className="text-gray-600 mb-6">Ihre Zahlung war erfolgreich. Sie haben jetzt Zugang zu allen Premium-Features!</p>
            <a
              href="/"
              className="bg-blue-500 hover:bg-blue-600 text-white font-medium py-3 px-6 rounded-lg transition-colors"
            >
              Zur App
            </a>
          </>
        )}
        
        {status === 'pending' && (
          <>
            <div className="text-6xl mb-4">⏳</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Zahlung wird verarbeitet...</h2>
            <p className="text-gray-600">Dies kann einige Sekunden dauern.</p>
          </>
        )}
        
        {status === 'error' && (
          <>
            <div className="text-6xl mb-4">❌</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Fehler bei der Zahlung</h2>
            <p className="text-gray-600 mb-6">Es gab ein Problem bei der Verarbeitung Ihrer Zahlung.</p>
            <a
              href="/"
              className="bg-gray-500 hover:bg-gray-600 text-white font-medium py-3 px-6 rounded-lg transition-colors"
            >
              Zurück zur App
            </a>
          </>
        )}
      </div>
    </div>
  );
};

// Main App Component
function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <BrowserRouter>
          <AuthWrapper />
        </BrowserRouter>
      </AuthProvider>
    </LanguageProvider>
  );
}

// Auth Wrapper to handle routing based on auth state
const AuthWrapper = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">⏰</div>
          <p className="text-gray-600">Laden...</p>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      <Route
        path="/subscription-success"
        element={user ? <SubscriptionSuccess /> : <Navigate to="/" />}
      />
      <Route
        path="/"
        element={user ? <Dashboard /> : <AuthPage />}
      />
    </Routes>
  );
};

export default App;