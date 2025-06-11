import type { DrugQuery, DrugResponse } from '../types/drug';

const API_URL = import.meta.env.VITE_API_URL || 'https://drug-interaction-api.onrender.com';

export const checkDrugInteractions = async (query: DrugQuery): Promise<DrugResponse> => {
    try {
        console.log('Sending request to API:', query);
        const response = await fetch(`${API_URL}/check-interactions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(query),
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error('API Error:', errorData);
            throw new Error(errorData.detail || 'Failed to check drug interactions');
        }

        const data = await response.json();
        console.log('Received response from API:', data);
        return data;
    } catch (error) {
        console.error('Error in checkDrugInteractions:', error);
        throw error;
    }
}; 