# Digital Triage - Patient Admission Form

## Overview
This is a multi-step form component for digital triage patient admission using advanced React patterns.

## Architecture

### Compound Components Pattern
The form uses the Compound Component pattern with Context API to manage state across steps:

- **WizardContext**: Provides step navigation state and controls
- **Wizard**: Wrapper component that manages overall state
- **WizardStep**: Individual step display component
- **WizardProgressBar**: Visual progress indicator
- **WizardNavigation**: Navigation controls (Previous/Next buttons)

### Form Management
- **react-hook-form**: For uncontrolled inputs and form state management
- **zod**: For schema validation with TypeScript type inference
- **@hookform/resolvers**: To integrate Zod with react-hook-form

## Features

### Three-Step Form
1. **Identification** (Step 1)
   - DNI/Document ID
   - First Name
   - Last Name
   - Date of Birth
   - Phone Contact

2. **Vital Signs** (Step 2)
   - Temperature (°C)
   - Heart Rate (bpm)
   - Blood Pressure Systolic (mmHg)
   - Blood Pressure Diastolic (mmHg)
   - Oxygen Saturation (%)
   - Weight (kg)

3. **Medical History** (Step 3)
   - Chronic Diseases (tag/chip selection)
   - Allergies (tag/chip selection)
   - Current Medications (textarea)
   - Current Symptoms (textarea)
   - Emergency Contact

### UX Features
- ✅ Progress bar showing current step and percentage
- ✅ Auto-save to localStorage (survives page refresh)
- ✅ Auto-restore from localStorage on mount
- ✅ Smart "Next" button - disabled when step is invalid
- ✅ Validation feedback with error messages
- ✅ Responsive design (mobile and desktop)
- ✅ Accessible tag/chip selection for diseases and allergies

## Testing
Tests are written using Vitest and React Testing Library:

- Form rendering and initial state
- Progress bar display
- Next button disabled/enabled based on validation
- Step navigation (forward and backward)
- localStorage save functionality
- localStorage restoration on mount

Run tests with:
```bash
npm test
```

## Usage

```tsx
import AdmissionForm from './features/admission/components/AdmissionForm'

function App() {
  return <AdmissionForm />
}
```

## File Structure
```
src/features/admission/
├── schemas.ts                      # Zod validation schemas
├── components/
│   ├── AdmissionForm.tsx          # Main form component
│   ├── AdmissionForm.test.tsx     # Tests
│   └── Wizard/
│       ├── WizardContext.tsx      # Context provider and components
│       └── WizardStep.tsx         # Step display component
```

## Form Submission
Currently, the form logs the submitted data to the console. Integration with backend API is pending.

Example output:
```json
{
  "identification": {
    "dni": "12345678",
    "firstName": "Juan",
    "lastName": "Pérez",
    "dateOfBirth": "1990-01-01",
    "phone": "1234567890"
  },
  "vitals": {
    "temperature": 36.5,
    "heartRate": 70,
    "bloodPressureSystolic": 120,
    "bloodPressureDiastolic": 80,
    "oxygenSaturation": 98,
    "weight": 70
  },
  "medicalHistory": {
    "chronicDiseases": ["Diabetes"],
    "allergies": ["Ninguna"],
    "currentMedications": "None",
    "symptoms": "Dolor de cabeza persistente",
    "emergencyContact": "9876543210"
  }
}
```

## Technical Details

### Performance Optimization
- Uncontrolled inputs via react-hook-form minimize re-renders
- Form state only updates on actual user input
- Compound components avoid prop drilling

### Type Safety
- Full TypeScript support with inferred types from Zod schemas
- Type-safe form values throughout the component tree

### Validation
- Real-time validation as user types
- Clear error messages for each field
- Step-level validation prevents progression with invalid data

## Future Enhancements
- [ ] Backend API integration
- [ ] Multi-language support
- [ ] Print/PDF export of completed form
- [ ] Admin dashboard for reviewing submissions
