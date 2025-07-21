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
  Copy
} from "lucide-react";
import "./App.css";
import axios from "axios";

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

// Login/Register Component
const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ email: '', password: '', name: '', referralCode: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login, register } = useAuth();

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
      setError(error.response?.data?.detail || 'Ein Fehler ist aufgetreten');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-lg p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            ⏰ Zeitgesteuerte Nachrichten
          </h1>
          <p className="text-gray-600">
            {isLogin ? 'Anmelden' : 'Registrieren'}
          </p>
        </div>

        {error && (
          <div className="bg-red-50 text-red-700 p-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Name
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Ihr Name"
                required
              />
            </div>
          )}
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              E-Mail
            </label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="ihre@email.de"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Passwort
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
            {loading ? 'Wird verarbeitet...' : (isLogin ? 'Anmelden' : 'Registrieren')}
          </button>
        </form>

        <div className="text-center mt-6">
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-blue-500 hover:text-blue-600"
          >
            {isLogin ? 'Noch kein Account? Registrieren' : 'Bereits registriert? Anmelden'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Header Component
const Header = ({ activeTab, setActiveTab }) => {
  const { user, logout } = useAuth();
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
              ⏰ Zeitgesteuerte Nachrichten
            </h1>
            <div className={`flex items-center space-x-2 px-3 py-1 rounded-full border ${getPlanColor(user.subscription_plan)}`}>
              {getPlanIcon(user.subscription_plan)}
              <span className="text-sm font-medium capitalize">{user.subscription_plan}</span>
            </div>
          </div>

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
                    <div className="text-xs text-gray-500">Nachrichten diesen Monat</div>
                    <div className="text-sm font-medium">
                      {user.monthly_messages_limit === -1 ? 
                        `${user.monthly_messages_used} (Unbegrenzt)` :
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
                    <span>Abo-Verwaltung</span>
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
                      <span>Admin Panel</span>
                    </button>
                  )}
                  <button
                    onClick={logout}
                    className="w-full flex items-center space-x-2 px-3 py-2 text-left text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Abmelden</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

// Main Dashboard Component
const Dashboard = () => {
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
  const { user, refreshUser } = useAuth();

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
    
    if (user?.role === 'admin') {
      fetchAdminStats();
      fetchAdminData();
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
              Nachricht erstellen
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
              Geplant ({scheduledMessages.length})
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
              Ausgeliefert ({deliveredMessages.length})
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
              Premium
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
                Admin
              </button>
            )}
          </div>
        </div>

        {/* Create Message Tab */}
        {activeTab === 'create' && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-semibold text-gray-800">
                Neue Nachricht erstellen
              </h2>
              <button
                onClick={() => setShowAiPanel(!showAiPanel)}
                className="flex items-center space-x-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg transition-colors"
              >
                <Wand2 className="w-4 h-4" />
                <span>AI-Assistent</span>
              </button>
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
                    <p className="font-medium text-yellow-800">Nachrichtenlimit erreicht</p>
                    <p className="text-sm text-yellow-700">
                      Sie haben Ihr monatliches Limit von {user.monthly_messages_limit} Nachrichten erreicht. 
                      Upgraden Sie auf Premium für unbegrenzte Nachrichten.
                    </p>
                  </div>
                </div>
              </div>
            )}

            <form onSubmit={createMessage} className="space-y-6">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Titel
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
                        <span>Verbessern</span>
                      </button>
                    </div>
                  )}
                </div>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({...formData, title: e.target.value})}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Gib deiner Nachricht einen Titel..."
                  required
                  disabled={isAtMessageLimit}
                />
              </div>
              
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Nachricht
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
                        <span>Verbessern</span>
                      </button>
                      <button
                        type="button"
                        onClick={async () => {
                          const corrected = await enhanceMessageWithAI(formData.content, "correct");
                          if (corrected) setFormData({...formData, content: corrected});
                        }}
                        className="text-xs text-green-600 hover:text-green-800 flex items-center space-x-1"
                      >
                        <CheckCircle className="w-3 h-3" />
                        <span>Korrigieren</span>
                      </button>
                    </div>
                  )}
                </div>
                <textarea
                  value={formData.content}
                  onChange={(e) => setFormData({...formData, content: e.target.value})}
                  rows="4"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Schreibe deine Nachricht hier... oder nutze den AI-Assistenten oben!"
                  required
                  disabled={isAtMessageLimit}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Lieferzeitpunkt
                </label>
                <input
                  type="datetime-local"
                  value={formData.scheduled_time}
                  onChange={(e) => setFormData({...formData, scheduled_time: e.target.value})}
                  min={getMinDateTime()}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                  disabled={isAtMessageLimit}
                />
              </div>

              {/* Recurring Options (Premium Feature) */}
              <div className="border-t pt-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <Repeat className="w-5 h-5 text-gray-500" />
                    <span className="text-sm font-medium text-gray-700">Wiederkehrende Nachricht</span>
                    {!canUseRecurring && <Crown className="w-4 h-4 text-yellow-500" />}
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.is_recurring}
                      onChange={(e) => setFormData({...formData, is_recurring: e.target.checked})}
                      className="sr-only peer"
                      disabled={!canUseRecurring || isAtMessageLimit}
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                {!canUseRecurring && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
                    <p className="text-sm text-blue-700">
                      <Crown className="w-4 h-4 inline mr-1" />
                      Wiederkehrende Nachrichten sind nur für Premium- und Business-Abonnenten verfügbar.
                    </p>
                  </div>
                )}

                {formData.is_recurring && canUseRecurring && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Wiederholungsintervall
                    </label>
                    <select
                      value={formData.recurring_pattern}
                      onChange={(e) => setFormData({...formData, recurring_pattern: e.target.value})}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      required
                      disabled={isAtMessageLimit}
                    >
                      <option value="">Intervall auswählen</option>
                      <option value="daily">Täglich</option>
                      <option value="weekly">Wöchentlich</option>
                      <option value="monthly">Monatlich</option>
                    </select>
                  </div>
                )}
              </div>
              
              <button
                type="submit"
                disabled={loading || isAtMessageLimit}
                className="w-full bg-blue-500 hover:bg-blue-600 text-white font-medium py-3 px-6 rounded-lg transition-colors disabled:opacity-50"
              >
                {loading ? '⏳ Wird erstellt...' : '📅 Nachricht planen'}
              </button>
            </form>
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
    <AuthProvider>
      <BrowserRouter>
        <AuthWrapper />
      </BrowserRouter>
    </AuthProvider>
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