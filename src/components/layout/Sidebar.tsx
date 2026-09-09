/**
 * INFINITE LOOPS — SIH26038
 * Clinical Workstation Sidebar (Collapsible, Only on Results Dashboard)
 */

import React from 'react';
import {
  LayoutDashboard,
  PlusCircle,
  FileCheck,
  FileText,
  LogOut,
  Eye,
  PanelLeftClose,
  PanelLeftOpen,
} from 'lucide-react';
import { useScreening } from '../../context/ScreeningContext';

interface SidebarProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, onToggleCollapse }) => {
  const { currentStep, startNewScreening, navigateToStep } = useScreening();

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, active: currentStep === 'clinical_results', onClick: () => navigateToStep('clinical_results') },
    { id: 'new_screening', label: 'New Screening', icon: PlusCircle, active: currentStep === 'session_start' || currentStep === 'acquisition', onClick: startNewScreening },
    { id: 'results', label: 'Results', icon: FileCheck, active: currentStep === 'clinical_results', onClick: () => navigateToStep('clinical_results') },
    { id: 'reports', label: 'Report Workspace', icon: FileText, active: currentStep === 'clinical_results', onClick: () => navigateToStep('clinical_results') },
  ];

  return (
    <aside
      className={`clinical-sidebar ${isCollapsed ? 'collapsed' : ''}`}
      style={{
        width: isCollapsed ? 68 : 240,
        minWidth: isCollapsed ? 68 : 240,
        transition: 'width 0.2s ease, min-width 0.2s ease',
      }}
    >
      <div>
        {/* Brand Header + Collapse Button */}
        <div className="sidebar-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div className="brand-badge">
            <div style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              backgroundColor: '#1d4ed8',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              flexShrink: 0,
            }}>
              <Eye size={18} strokeWidth={2.2} />
            </div>
            {!isCollapsed && (
              <div className="brand-text">
                <div className="brand-title">INFINITE LOOPS</div>
                <div className="brand-subtitle">AI Retinal Screening</div>
              </div>
            )}
          </div>

          <button
            type="button"
            onClick={onToggleCollapse}
            title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-sidebar-muted)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 4,
              borderRadius: 4,
            }}
          >
            {isCollapsed ? <PanelLeftOpen size={17} /> : <PanelLeftClose size={17} />}
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="sidebar-nav">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                type="button"
                onClick={item.onClick}
                className={`sidebar-nav-item ${item.active ? 'active' : ''}`}
                style={{
                  background: 'none',
                  border: 'none',
                  width: '100%',
                  textAlign: 'left',
                  justifyContent: isCollapsed ? 'center' : 'flex-start',
                  padding: isCollapsed ? '10px 0' : '9px 12px',
                }}
                title={isCollapsed ? item.label : undefined}
              >
                <Icon size={18} strokeWidth={2} style={{ flexShrink: 0 }} />
                {!isCollapsed && <span>{item.label}</span>}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Doctor Profile Footer */}
      <div className="sidebar-footer">
        <div className="doctor-profile-card" style={{ justifyContent: isCollapsed ? 'center' : 'flex-start' }}>
          <div className="doctor-avatar" style={{ flexShrink: 0 }}>DR</div>
          {!isCollapsed && (
            <div className="doctor-profile-info">
              <div className="doctor-name">Dr. Sharma</div>
              <div className="doctor-role">Ophthalmologist</div>
            </div>
          )}
        </div>
        {!isCollapsed && (
          <button
            type="button"
            className="sidebar-nav-item"
            style={{ width: '100%', padding: '6px 8px', fontSize: 12, background: 'none', border: 'none' }}
            onClick={() => alert('Workstation session locked for Dr. Sharma.')}
          >
            <LogOut size={15} />
            <span>Log out</span>
          </button>
        )}
      </div>
    </aside>
  );
};
