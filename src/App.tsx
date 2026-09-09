/**
 * INFINITE LOOPS — SIH26038
 * Root Application Component
 */

import React from 'react';
import { ScreeningProvider } from './context/ScreeningContext';
import { AppShell } from './components/layout/AppShell';

export const App: React.FC = () => {
  return (
    <ScreeningProvider>
      <AppShell />
    </ScreeningProvider>
  );
};

export default App;
