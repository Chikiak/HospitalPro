import React, { type ReactNode } from 'react';
import { useWizard } from './WizardContext';

interface WizardStepProps {
  step: number;
  children: ReactNode;
  title: string;
  description?: string;
}

const WizardStep: React.FC<WizardStepProps> = ({ step, children, title, description }) => {
  const { currentStep } = useWizard();

  if (currentStep !== step) {
    return null;
  }

  return (
    <div className="w-full">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">{title}</h2>
        {description && <p className="text-gray-600">{description}</p>}
      </div>
      {children}
    </div>
  );
};

export default WizardStep;
