import React, { createContext, useContext, useState, useEffect } from 'react';
import { TCGType } from '../utils/tcgCategories';

interface TCGContextType {
  selectedTCG: TCGType;
  setSelectedTCG: (tcg: TCGType) => void;
}

const TCGContext = createContext<TCGContextType | undefined>(undefined);

export const TCGProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [selectedTCG, setSelectedTCGState] = useState<TCGType>(() => {
    const saved = localStorage.getItem('selectedTCG');
    return (saved as TCGType) || 'all';
  });

  const setSelectedTCG = (tcg: TCGType) => {
    setSelectedTCGState(tcg);
    localStorage.setItem('selectedTCG', tcg);
  };

  useEffect(() => {
    localStorage.setItem('selectedTCG', selectedTCG);
  }, [selectedTCG]);

  return (
    <TCGContext.Provider value={{ selectedTCG, setSelectedTCG }}>
      {children}
    </TCGContext.Provider>
  );
};

export const useTCG = () => {
  const context = useContext(TCGContext);
  if (context === undefined) {
    throw new Error('useTCG must be used within a TCGProvider');
  }
  return context;
};
