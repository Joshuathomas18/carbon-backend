const API_BASE_URL = 'http://localhost:8000/api/v1';

/**
 * Estimate carbon for a plot.
 * @param {Object} params - { lat, lon, area_hectares, language }
 */
export const estimateCarbon = async (params) => {
  try {
    const response = await fetch(`${API_BASE_URL}/plots/estimate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to estimate carbon');
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

/**
 * Send voice query to the assistant.
 * @param {string} audioBase64 - Base64 encoded audio
 * @param {string} language - hi, kn, pa, en
 */
export const sendVoiceQuery = async (audioBase64, language = 'en') => {
  try {
    const response = await fetch(`${API_BASE_URL}/voice/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        audio_base64: audioBase64,
        language,
      }),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to process voice query');
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};
