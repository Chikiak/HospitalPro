/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useContext, useState, type ReactNode } from 'react';

interface WizardContextType {
  currentStep: number;
  totalSteps: number;
  goToNext: () => void;
  goToPrevious: () => void;
  goToStep: (step: number) => void;
  canGoNext: boolean;
  setCanGoNext: (canGo: boolean) => void;
}

const WizardContext = createContext<WizardContextType | undefined>(undefined);

export const useWizard = () => {
  const context = useContext(WizardContext);
  if (!context) {
    throw new Error('useWizard must be used within a Wizard component');
  }
  return context;
};

interface WizardProps {
  children: ReactNode;
  totalSteps: number;
  onComplete?: () => void;
}

export const Wizard: React.FC<WizardProps> = ({ children, totalSteps, onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [canGoNext, setCanGoNext] = useState(false);

  const goToNext = () => {
    if (currentStep < totalSteps - 1) {
      setCurrentStep(currentStep + 1);
      setCanGoNext(false);
    } else if (onComplete) {
      onComplete();
    }
  };

  const goToPrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const goToStep = (step: number) => {
    if (step >= 0 && step < totalSteps) {
      setCurrentStep(step);
      setCanGoNext(false);
    }
  };

  return (
    <WizardContext.Provider
      value={{
        currentStep,
        totalSteps,
        goToNext,
        goToPrevious,
        goToStep,
        canGoNext,
        setCanGoNext,
      }}
    >
      {children}
    </WizardContext.Provider>
  );
};

interface WizardProgressBarProps {
  className?: string;
}

export const WizardProgressBar: React.FC<WizardProgressBarProps> = ({ className = '' }) => {
  const { currentStep, totalSteps } = useWizard();
  const progress = ((currentStep + 1) / totalSteps) * 100;

  return (
    <div className={`w-full ${className}`}>
      <div className="flex justify-between mb-2">
        <span className="text-sm font-medium text-gray-700">
          Paso {currentStep + 1} de {totalSteps}
        </span>
        <span className="text-sm font-medium text-blue-600">
          {Math.round(progress)}%
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2.5">
        <div
          className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
};

interface WizardNavigationProps {
  onSave?: () => void;
  isLastStep?: boolean;
  className?: string;
}

export const WizardNavigation: React.FC<WizardNavigationProps> = ({
  onSave,
  isLastStep = false,
  className = '',
}) => {
  const { currentStep, goToNext, goToPrevious, canGoNext } = useWizard();

  return (
    <div className={`flex justify-between gap-4 ${className}`}>
      <button
        type="button"
        onClick={goToPrevious}
        disabled={currentStep === 0}
        className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        Anterior
      </button>
      <div className="flex gap-2">
        {onSave && (
          <button
            type="button"
            onClick={onSave}
            className="px-6 py-2 border border-blue-300 text-blue-600 rounded-lg font-medium hover:bg-blue-50 transition-colors"
          >
            Guardar Borrador
          </button>
        )}
        <button
          type="button"
          onClick={goToNext}
          disabled={!canGoNext}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLastStep ? 'Enviar' : 'Siguiente'}
        </button>
      </div>
    </div>
  );
};
