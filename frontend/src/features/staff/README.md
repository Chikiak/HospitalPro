# Excel Export Feature

## Overview
This feature allows staff members to export patient data to Excel format for easy data transfer to the Oracle-based medical records system.

## Component Location
`frontend/src/features/staff/ExportExcel.tsx`

## How to Use

### In the Application
1. Navigate to the staff section
2. Import and use the `ExportExcel` component:
   ```tsx
   import ExportExcel from '../features/staff/ExportExcel';
   
   function StaffDashboard() {
     return (
       <div>
         <ExportExcel />
       </div>
     );
   }
   ```
3. Click the "Descargar Excel" button
4. The file will download automatically with the format `pacientes_YYYY-MM-DD.xlsx`

## Excel File Contents

The exported Excel file includes the following columns:

| Column | Description |
|--------|-------------|
| ID | Patient ID in the system |
| DNI | Patient DNI/Cedula (11 digits) |
| Paciente | Patient's full name |
| Estado | Active/Inactive status |
| Alergias | Patient allergies (if provided) |
| Enfermedades Crónicas | Chronic diseases from medical history |
| Cirugías Previas | Previous surgeries |
| Medicación Actual | Current medications |
| Antecedentes Familiares | Family medical history |
| Hábitos | Patient habits |
| Otros Datos Médicos | Other medical information |

## Backend API

### Endpoint
`GET /patients/`

### Response Format
```json
[
  {
    "id": 1,
    "dni": "12345678901",
    "full_name": "Juan Pérez",
    "is_active": true,
    "medical_history": {
      "chronic_diseases": "Diabetes",
      "current_medications": "Metformin",
      "previous_surgeries": "None",
      "family_history": "Diabetes (father)",
      "habits": "Non-smoker",
      "other_medical_info": "Regular checkups"
    },
    "allergies": "Penicillin"
  }
]
```

### Performance
- Uses optimized LEFT JOIN query to fetch all data in a single database round-trip
- Efficient for large datasets

## Security Considerations

⚠️ **Important Security Notes:**

1. **Authentication Required (TODO)**: This endpoint currently does not have authentication/authorization. Before deploying to production, implement middleware to verify that:
   - The user is authenticated
   - The user has the role: `staff`, `admin`, or `doctor`

2. **Data Sensitivity**: The exported file contains sensitive medical information. Users should:
   - Handle files according to hospital privacy policies
   - Not share files via insecure channels
   - Delete files after transferring to the medical records system

3. **Library Vulnerabilities**: The xlsx library (v0.18.5) has known vulnerabilities but is the latest available on npm. Consider:
   - Upgrading when newer versions become available
   - Using alternative libraries like `exceljs` if security is critical
   - Server-side generation using Python's `openpyxl` as mentioned in the README

## Use Case

As described in the project README:

> "When a new patient comes to consultation, the doctor **does not need to ask again or manually type** their background information. The system allows downloading a structured **Excel (.xlsx) file** with all the information that the patient entered during registration (allergies, medical history, etc.). The doctor can copy and paste this data directly into the Clinical History system (Oracle), saving valuable consultation minutes."

## Future Enhancements

- [ ] Add authentication/authorization middleware
- [ ] Allow filtering by date range
- [ ] Add option to export selected patients only
- [ ] Support for additional export formats (CSV, PDF)
- [ ] Upgrade to more secure Excel library when available
