import { useState } from 'react';
import { 
  Plane, Hotel, Cloud, DollarSign, Calendar, MapPin, 
  Download, Printer, Clock, TrendingUp, AlertCircle,
  CheckCircle, Star, Navigation
} from 'lucide-react';
import './TravelPlanDisplay.css';

interface TravelPlanDisplayProps {
  content: string;
  threadId?: string;
  latency?: number;
}

interface ParsedSection {
  title: string;
  content: string;
  icon: JSX.Element;
  type: 'flight' | 'hotel' | 'weather' | 'budget' | 'itinerary' | 'summary' | 'recommendations';
}

const TravelPlanDisplay = ({ content, threadId, latency }: TravelPlanDisplayProps) => {
  const [activeTab, setActiveTab] = useState<string>('overview');

  const parseContent = (): ParsedSection[] => {
    const sections: ParsedSection[] = [];
    const lines = content.split('\n');
    
    let currentSection: ParsedSection | null = null;
    let currentContent: string[] = [];

    const getSectionIcon = (title: string): { icon: JSX.Element; type: any } => {
      const lowerTitle = title.toLowerCase();
      if (lowerTitle.includes('flight') || lowerTitle.includes('✈')) return { icon: <Plane />, type: 'flight' };
      if (lowerTitle.includes('hotel') || lowerTitle.includes('accommodation') || lowerTitle.includes('🏨')) return { icon: <Hotel />, type: 'hotel' };
      if (lowerTitle.includes('weather') || lowerTitle.includes('climate') || lowerTitle.includes('☀')) return { icon: <Cloud />, type: 'weather' };
      if (lowerTitle.includes('budget') || lowerTitle.includes('cost') || lowerTitle.includes('💰')) return { icon: <DollarSign />, type: 'budget' };
      if (lowerTitle.includes('itinerary') || lowerTitle.includes('day') || lowerTitle.includes('schedule') || lowerTitle.includes('📅')) return { icon: <Calendar />, type: 'itinerary' };
      if (lowerTitle.includes('recommendation') || lowerTitle.includes('tips') || lowerTitle.includes('advice')) return { icon: <Star />, type: 'recommendations' };
      if (lowerTitle.includes('summary') || lowerTitle.includes('overview')) return { icon: <MapPin />, type: 'summary' };
      return { icon: <Navigation />, type: 'summary' };
    };

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // Detect section headers (markdown headers or numbered headers)
      if (line.match(/^#{1,3}\s+/) || line.match(/^\d+\.\s+[A-Z]/)) {
        // Save previous section
        if (currentSection && currentContent.length > 0) {
          currentSection.content = currentContent.join('\n');
          sections.push(currentSection);
          currentContent = [];
        }

        // Start new section
        const title = line.replace(/^#{1,3}\s+/, '').replace(/^\d+\.\s+/, '').trim();
        const { icon, type } = getSectionIcon(title);
        currentSection = { title, content: '', icon, type };
      } else if (currentSection) {
        currentContent.push(line);
      } else {
        // Content before first section
        currentContent.push(line);
      }
    }

    // Save last section
    if (currentSection && currentContent.length > 0) {
      currentSection.content = currentContent.join('\n');
      sections.push(currentSection);
    } else if (currentContent.length > 0) {
      // If no sections were found, treat everything as one section
      sections.push({
        title: 'Travel Plan',
        content: currentContent.join('\n'),
        icon: <MapPin />,
        type: 'summary'
      });
    }

    return sections;
  };

  const sections = parseContent();

  const handleDownload = () => {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `travel-plan-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handlePrint = () => {
    window.print();
  };

  const renderTable = (tableText: string) => {
    const lines = tableText.trim().split('\n');
    if (lines.length < 3) return <pre>{tableText}</pre>;

    // Find table lines (contains |)
    const tableLines = lines.filter(line => line.includes('|'));
    if (tableLines.length < 2) return <pre>{tableText}</pre>;

    const parseRow = (line: string) => 
      line.split('|').map(cell => cell.trim()).filter(cell => cell);

    const headers = parseRow(tableLines[0]);
    const rows = tableLines.slice(2).map(parseRow); // Skip separator line

    return (
      <div className="table-container">
        <table className="travel-table">
          <thead>
            <tr>
              {headers.map((header, i) => (
                <th key={i}>{header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i}>
                {row.map((cell, j) => (
                  <td key={j}>{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderContent = (content: string) => {
    // Check if content contains tables
    if (content.includes('|') && content.includes('---')) {
      const parts = content.split('\n\n');
      return parts.map((part, i) => {
        if (part.includes('|') && part.includes('---')) {
          return <div key={i}>{renderTable(part)}</div>;
        }
        return <div key={i} className="content-block" dangerouslySetInnerHTML={{ __html: formatText(part) }} />;
      });
    }

    return <div className="content-block" dangerouslySetInnerHTML={{ __html: formatText(content) }} />;
  };

  const formatText = (text: string): string => {
    return text
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/₹/g, '<span class="currency">₹</span>')
      .replace(/\$(\d+)/g, '<span class="currency">$$$1</span>')
      .replace(/^\-\s+(.+)$/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>\n?)+/g, '<ul class="travel-list">$&</ul>')
      .replace(/\n/g, '<br/>');
  };

  const getSectionColor = (type: string): string => {
    const colors: Record<string, string> = {
      flight: '#3b82f6',
      hotel: '#8b5cf6',
      weather: '#06b6d4',
      budget: '#f59e0b',
      itinerary: '#10b981',
      summary: '#6366f1',
      recommendations: '#ec4899'
    };
    return colors[type] || '#6366f1';
  };

  const Overview = () => (
    <div className="overview-grid">
      {sections.slice(0, 4).map((section, index) => (
        <div 
          key={index} 
          className="overview-card"
          style={{ borderTopColor: getSectionColor(section.type) }}
        >
          <div className="overview-icon" style={{ color: getSectionColor(section.type) }}>
            {section.icon}
          </div>
          <h4>{section.title}</h4>
          <div className="overview-preview">
            {section.content.split('\n').slice(0, 3).join(' ').substring(0, 120)}...
          </div>
          <button 
            className="view-details-btn"
            onClick={() => setActiveTab(section.type)}
          >
            View Details →
          </button>
        </div>
      ))}
    </div>
  );

  return (
    <div className="travel-plan-display">
      {/* Header */}
      <div className="plan-header">
        <div className="plan-header-content">
          <div className="plan-icon-large">
            <MapPin size={32} />
          </div>
          <div>
            <h2 className="plan-title">Your AI Travel Plan</h2>
            <div className="plan-meta">
              {threadId && <span className="meta-item">ID: {threadId.slice(0, 12)}</span>}
              {latency && (
                <span className="meta-item">
                  <Clock size={14} />
                  {latency.toFixed(1)}s
                </span>
              )}
              <span className="meta-item success">
                <CheckCircle size={14} />
                Ready to Book
              </span>
            </div>
          </div>
        </div>
        <div className="plan-actions">
          <button className="action-btn" onClick={handleDownload} title="Download plan">
            <Download size={18} />
            <span>Download</span>
          </button>
          <button className="action-btn" onClick={handlePrint} title="Print plan">
            <Printer size={18} />
            <span>Print</span>
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="plan-tabs">
        <button 
          className={`plan-tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <Navigation size={18} />
          Overview
        </button>
        {sections.map((section, index) => (
          <button
            key={index}
            className={`plan-tab ${activeTab === section.type ? 'active' : ''}`}
            onClick={() => setActiveTab(section.type)}
            style={activeTab === section.type ? { borderBottomColor: getSectionColor(section.type) } : {}}
          >
            {section.icon}
            {section.title}
          </button>
        ))}
      </div>

      {/* Content Area */}
      <div className="plan-content">
        {activeTab === 'overview' ? (
          <Overview />
        ) : (
          sections
            .filter(section => section.type === activeTab)
            .map((section, index) => (
              <div key={index} className="section-detail">
                <div className="section-header-detail">
                  <div 
                    className="section-icon-large" 
                    style={{ backgroundColor: `${getSectionColor(section.type)}15`, color: getSectionColor(section.type) }}
                  >
                    {section.icon}
                  </div>
                  <div>
                    <h3>{section.title}</h3>
                    <p className="section-description">Detailed information and recommendations</p>
                  </div>
                </div>
                <div className="section-content">
                  {renderContent(section.content)}
                </div>
              </div>
            ))
        )}
      </div>

      {/* Quick Stats Footer */}
      <div className="plan-footer">
        <div className="quick-stats">
          <div className="stat-item">
            <TrendingUp size={16} />
            <span>AI-Optimized</span>
          </div>
          <div className="stat-item">
            <AlertCircle size={16} />
            <span>Prices Approximate</span>
          </div>
          <div className="stat-item">
            <CheckCircle size={16} />
            <span>Human-Reviewed</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TravelPlanDisplay;
