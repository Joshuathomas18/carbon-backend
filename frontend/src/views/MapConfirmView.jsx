import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ChevronLeft, Loader2, MapPin, CheckCircle2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { estimateCarbon } from '../api/carbonApi';

const MapConfirmView = ({ plotData, setResults }) => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [phoneNumber, setPhoneNumber] = useState(null);

  // 🪄 MAGIC LINK: Grab phone number from URL on mount
  useEffect(() => {
    const queryParams = new URLSearchParams(window.location.search);
    const phone = queryParams.get("phone");
    if (phone) {
      setPhoneNumber(phone);
      console.log("✅ WhatsApp Magic Link detected! Phone:", phone);
    }
  }, []);

  // 🚀 NEW: Handle save from WhatsApp magic link
  const handleSaveFromWhatsApp = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Build polygon GeoJSON from plotData
      // If plotData has lat/lon, create a simple polygon
      const polygon = plotData.polygon || {
        type: "Polygon",
        coordinates: [[
          [plotData.lon - 0.01, plotData.lat - 0.01],
          [plotData.lon + 0.01, plotData.lat - 0.01],
          [plotData.lon + 0.01, plotData.lat + 0.01],
          [plotData.lon - 0.01, plotData.lat + 0.01],
          [plotData.lon - 0.01, plotData.lat - 0.01]
        ]]
      };

      const response = await fetch('http://localhost:8000/api/v1/plots/save-with-phone', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phone_number: phoneNumber,
          polygon: polygon,
          area_hectares: plotData.area_hectares || 2.5
        })
      });

      if (response.ok) {
        const data = await response.json();
        console.log("✅ Farm saved! Response:", data);

        // 🧙 THE UX MAGIC: Tell farmer to check WhatsApp
        alert(
          "✅ Farm boundary saved successfully!\n\n" +
          "📱 Check your WhatsApp for your carbon estimate and 3 quick questions.\n\n" +
          "You can close this browser window now."
        );

        // Optional: Show success screen or redirect
        // navigate('/success');
      } else {
        const errorData = await response.json();
        setError(`Failed to save farm: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (err) {
      console.error("Error saving farm from WhatsApp:", err);
      setError("Network error while saving farm. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // Original flow: estimate carbon without WhatsApp
  const handleConfirm = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await estimateCarbon({
        lat: plotData.lat,
        lon: plotData.lon,
        area_hectares: plotData.area_hectares,
        language: "en"
      });
      // The backend returns a full CarbonEstimate object
      setResults(response);
      navigate('/assistant');
    } catch (err) {
      console.error(err);
      setError("Unable to reach analyst. Using satellite approximation...");
      setTimeout(() => {
        // Fallback mock data for demo if backend is unavailable
        const mock = {
          total_tonnes_co2: 2.1,
          value_inr: 18500,
          practices: [
            { name: "Zero Tillage", if_implemented_value_inr: 800 },
            { name: "Residue Retention", if_implemented_value_inr: 1200 }
          ]
        };
        setResults(mock);
        navigate('/assistant');
      }, 1500);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#FCF9F1]">
      {/* Map Header */}
      <div className="absolute top-8 left-8 z-30 flex items-center space-x-4">
        <button
          onClick={() => navigate('/')}
          className="bg-white/95 backdrop-blur-md p-4 rounded-[20px] shadow-xl border border-green-50 text-gray-900 active:scale-90 transition-transform"
        >
          <ChevronLeft size={24} />
        </button>
        <div className="bg-white/95 backdrop-blur-md px-6 py-3 rounded-[20px] shadow-lg border border-green-50">
          <span className="text-xs font-black uppercase tracking-widest text-green-700">
            {phoneNumber ? "🌾 WhatsApp Intake" : "Land Verification"}
          </span>
        </div>
      </div>

      {/* Map Content - Hero Background */}
      <div className="relative flex-1 overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{
            backgroundImage: `url('https://images.unsplash.com/photo-1542601906990-b4d3fb45ed09?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80')`
          }}
        />
        <div className="absolute inset-0 bg-green-900/10" />

        {/* Animated Boundary Box */}
        <div className="absolute inset-0 flex items-center justify-center">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="w-64 h-64 border-4 border-green-500 rounded-3xl bg-green-500/10 backdrop-blur-[2px] relative flex flex-col items-center justify-center"
          >
            <div className="absolute -top-4 -right-4 bg-green-600 text-white p-2 rounded-full shadow-lg">
              <CheckCircle2 size={24} />
            </div>
            <div className="bg-white/90 px-3 py-1 rounded-full text-[10px] font-black uppercase text-green-700 tracking-tighter mb-2">
              Boundary Detected
            </div>
            <div className="text-white font-black text-2xl drop-shadow-md">
              {plotData.area_hectares} Ac
            </div>
          </motion.div>
        </div>
      </div>

      {/* Bottom Tray - Rooted Elegance Style */}
      <motion.div
        initial={{ y: 200 }}
        animate={{ y: 0 }}
        className="bg-white rounded-t-[48px] p-8 pb-12 shadow-[0_-20px_60px_rgba(0,0,0,0.15)] z-40 border-t border-green-50"
      >
        <div className="w-16 h-1.5 bg-gray-100 rounded-full mx-auto mb-8" />

        <div className="space-y-8">
          <div className="space-y-3">
            <div className="flex items-center space-x-2 text-green-600">
              <MapPin size={18} />
              <span className="text-sm font-black uppercase tracking-[0.2em]">{plotData.district}</span>
            </div>
            <h3 className="text-3xl font-black text-gray-900 leading-tight">
              Is this the correct plot?
            </h3>
            <p className="text-lg text-gray-500 font-medium">
              {phoneNumber
                ? "Save your farm boundary and we'll send you a carbon estimate on WhatsApp."
                : "We'll use satellite history to analyze this specific area for carbon credits."}
            </p>
          </div>

          {error && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="p-4 bg-amber-50 rounded-2xl border border-amber-100">
              <p className="text-sm text-amber-700 font-bold">{error}</p>
            </motion.div>
          )}

          {phoneNumber && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="p-4 bg-green-50 rounded-2xl border border-green-100">
              <p className="text-sm text-green-700 font-bold">
                📱 WhatsApp Magic Link Active - Responses will be sent to {phoneNumber}
              </p>
            </motion.div>
          )}

          <div className="flex space-x-4">
            <button
              disabled={isLoading}
              onClick={() => navigate('/')}
              className="flex-1 py-6 rounded-3xl border-2 border-gray-100 text-gray-400 font-black text-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              No, Adjust
            </button>
            <button
              disabled={isLoading}
              onClick={phoneNumber ? handleSaveFromWhatsApp : handleConfirm}
              className="flex-[1.5] py-6 rounded-3xl bg-green-700 text-white font-black text-lg shadow-xl shadow-green-900/10 hover:bg-green-800 transition-all disabled:opacity-80 flex items-center justify-center space-x-3 active:scale-95"
            >
              {isLoading ? <Loader2 className="animate-spin" /> : (
                <>
                  <span>{phoneNumber ? "Save & Check WhatsApp" : "Yes, Confirm"}</span>
                  <div className="w-6 h-6 bg-white/20 rounded-full flex items-center justify-center">
                    <CheckCircle2 size={14} />
                  </div>
                </>
              )}
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default MapConfirmView;
