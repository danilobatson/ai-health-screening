import { z } from 'zod';

// Symptom validation schema
export const symptomSchema = z.object({
  name: z.string()
    .min(2, 'Symptom name must be at least 2 characters')
    .max(100, 'Symptom name too long')
    .regex(/^[a-zA-Z\s\-]+$/, 'Symptom name can only contain letters, spaces, and hyphens'),
  severity: z.enum(['mild', 'moderate', 'severe'], {
    errorMap: () => ({ message: 'Severity must be mild, moderate, or severe' })
  }),
  duration_days: z.number()
    .int('Duration must be a whole number')
    .min(1, 'Duration must be at least 1 day')
    .max(365, 'Duration cannot exceed 365 days')
});

// Main health assessment schema
export const healthAssessmentSchema = z.object({
  name: z.string()
    .min(2, 'Name must be at least 2 characters')
    .max(100, 'Name too long')
    .regex(/^[a-zA-Z\s\-'\.]+$/, 'Name can only contain letters, spaces, hyphens, apostrophes, and periods'),
  age: z.number()
    .int('Age must be a whole number')
    .min(1, 'Age must be at least 1')
    .max(120, 'Age cannot exceed 120 years'),
  symptoms: z.array(symptomSchema)
    .min(1, 'At least one symptom is required')
    .max(10, 'Cannot exceed 10 symptoms'),
  medicalHistory: z.array(z.string())
    .max(20, 'Too many medical conditions selected')
});

// Medical history options (for validation)
export const VALID_MEDICAL_CONDITIONS = [
  'hypertension', 'diabetes', 'heart disease', 'asthma',
  'high cholesterol', 'obesity', 'anxiety', 'depression',
  'arthritis', 'allergies', 'cancer', 'stroke'
];

// Symptom name validation (for security)
export const VALID_SYMPTOM_NAMES = [
  'chest pain', 'shortness of breath', 'dizziness', 'headache',
  'nausea', 'fatigue', 'fever', 'cough', 'abdominal pain',
  'back pain', 'joint pain', 'muscle pain', 'swelling',
  'rash', 'vision changes', 'hearing problems'
];

// Validate symptom name against whitelist
export const validateSymptomName = (name) => {
  const normalized = name.toLowerCase().trim();
  return VALID_SYMPTOM_NAMES.includes(normalized) || 
         VALID_SYMPTOM_NAMES.some(valid => normalized.includes(valid.split(' ')[0]));
};
