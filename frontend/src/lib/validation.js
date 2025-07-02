import { z } from 'zod';

export const healthAssessmentSchema = z.object({
  name: z.string()
    .min(2, 'Name must be at least 2 characters')
    .max(100, 'Name too long'),
  
  age: z.number()
    .min(1, 'Age must be at least 1')
    .max(120, 'Age must be less than 120 years')
    .int('Age must be a whole number'),
  
  gender: z.enum(['male', 'female', 'other', 'prefer-not-to-say'], {
    errorMap: () => ({ message: 'Please select a gender' })
  }),
  
  symptoms: z.string()
    .min(10, 'Please provide more detail about your symptoms (minimum 10 characters)')
    .max(1000, 'Symptom description too long'),
  
  medical_history: z.string()
    .max(500, 'Medical history description too long')
    .optional(),
  
  current_medications: z.string()
    .max(500, 'Medication list too long')
    .optional()
});

export const validateHealthAssessment = (data) => {
  try {
    const validated = healthAssessmentSchema.parse({
      ...data,
      age: parseInt(data.age),
      medical_history: data.medical_history || '',
      current_medications: data.current_medications || ''
    });
    return { success: true, data: validated };
  } catch (error) {
    return { 
      success: false, 
      errors: error.errors.reduce((acc, err) => {
        acc[err.path[0]] = err.message;
        return acc;
      }, {})
    };
  }
};
