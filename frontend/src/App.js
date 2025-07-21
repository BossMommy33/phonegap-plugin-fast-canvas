import { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [messages, setMessages] = useState([]);
  const [activeTab, setActiveTab] = useState('create');
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    scheduled_time: ''
  });
  const [loading, setLoading] = useState(false);

  // Fetch messages
  const fetchMessages = async () => {
    try {
      const response = await axios.get(`${API}/messages`);
      setMessages(response.data);
    } catch (error) {
      console.error('Error fetching messages:', error);
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
      setFormData({ title: '', content: '', scheduled_time: '' });
      fetchMessages();
      setActiveTab('scheduled');
    } catch (error) {
      console.error('Error creating message:', error);
      alert('Fehler beim Erstellen der Nachricht!');
    } finally {
      setLoading(false);
    }
  };

  // Delete message
  const deleteMessage = async (messageId) => {
    try {
      await axios.delete(`${API}/messages/${messageId}`);
      fetchMessages();
    } catch (error) {
      console.error('Error deleting message:', error);
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

  useEffect(() => {
    fetchMessages();
    // Refresh messages every 10 seconds to show delivered messages
    const interval = setInterval(fetchMessages, 10000);
    return () => clearInterval(interval);
  }, []);

  const scheduledMessages = getMessagesByStatus('scheduled');
  const deliveredMessages = getMessagesByStatus('delivered');

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-800 mb-2">
              ⏰ Zeitgesteuerte Nachrichten
            </h1>
            <p className="text-lg text-gray-600">
              Erstelle Nachrichten und lass sie zur gewünschten Zeit ausliefern
            </p>
          </div>

          {/* Tab Navigation */}
          <div className="bg-white rounded-xl shadow-lg p-2 mb-6">
            <div className="flex space-x-1">
              <button
                onClick={() => setActiveTab('create')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === 'create'
                    ? 'bg-blue-500 text-white shadow-md'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                ✏️ Nachricht erstellen
              </button>
              <button
                onClick={() => setActiveTab('scheduled')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === 'scheduled'
                    ? 'bg-blue-500 text-white shadow-md'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                ⏳ Geplant ({scheduledMessages.length})
              </button>
              <button
                onClick={() => setActiveTab('delivered')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === 'delivered'
                    ? 'bg-blue-500 text-white shadow-md'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                ✅ Ausgeliefert ({deliveredMessages.length})
              </button>
            </div>
          </div>

          {/* Create Message Tab */}
          {activeTab === 'create' && (
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-2xl font-semibold text-gray-800 mb-6">
                Neue Nachricht erstellen
              </h2>
              <form onSubmit={createMessage} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Titel
                  </label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({...formData, title: e.target.value})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Gib deiner Nachricht einen Titel..."
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nachricht
                  </label>
                  <textarea
                    value={formData.content}
                    onChange={(e) => setFormData({...formData, content: e.target.value})}
                    rows="4"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Schreibe deine Nachricht hier..."
                    required
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
                  />
                </div>
                
                <button
                  type="submit"
                  disabled={loading}
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
                              <span className="mr-2">🔔</span>
                            )}
                            {message.title}
                          </h3>
                          <p className="text-sm text-gray-600 mt-1">
                            📅 {formatDate(message.scheduled_time)}
                          </p>
                        </div>
                        <button
                          onClick={() => deleteMessage(message.id)}
                          className="text-red-500 hover:text-red-700 p-1"
                          title="Nachricht löschen"
                        >
                          🗑️
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
                            ✅ {message.title}
                          </h3>
                          <div className="text-sm text-gray-600 mt-1 space-y-1">
                            <p>📅 Geplant: {formatDate(message.scheduled_time)}</p>
                            <p>🚀 Ausgeliefert: {formatDate(message.delivered_at)}</p>
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
        </div>
      </div>
    </div>
  );
}

export default App;