"""Internationalization service for Carbon Kheth WhatsApp bot."""

MESSAGES = {
    "hinglish": {
        "welcome": "Welcome to Carbon_kheth! 🌱 Kripya apni bhasha chunein 👇\n\n1. Hinglish\n2. English\n3. हिंदी (Hindi)",
        "greeting": "Namaste! 🙏 Main aapke khet ka carbon score nikal sakta hoon — aur bataunga ki aap carbon credits se kitna kama sakte hain. Sirf 2 minute lagenge.\n\nShuru karein?\n1. Haan, shuru karo\n2. Pehle batao kya hai ye",
        "about": "Carbon credits kisanon ko unki achhi practices (jaise parali na jalana) ke liye paise dete hain. Hum satellite se aapka score check karenge.",
        "location_prompt": "Pehle apne khet ki location share karein 📍 (Neeche paperclip 📎 icon dabayein -> Location -> 'Share Current Location'). Agar aap khet pe nahi hain, toh kripya wahan ja kar share karein.",
        "location_confirm": "📍 Humne note kiya: {name} — sahi hai?\n1. Haan\n2. Nahi, change karo",
        "area_prompt": "Aapke khet ka area kitna hai? (Bigha, acre, ya hectare mein bata sakte hain)\n\nYa accurate result ke liye ye map link use karein: {link}",
        "area_retry": "Samajh nahi aaya 😅 Kripya area sahi se likhein (jaise: 5 acre ya 2.5 hectare).",
        "crop_prompt": "Is mausam mein kya uga rahe hain aap?\n1. Gehun (Wheat)\n2. Dhan (Paddy)\n3. Makka (Maize)\n4. Kuch aur",
        "urea_prompt": "Ek season mein kitne bag Urea use karte hain?\n1. 0-2 bags\n2. 3-5 bags\n3. 6-10 bags\n4. 10+ bags",
        "burning_prompt": "Kya aap parali jalate hain harvest ke baad?\n1. Haan\n2. Nahi\n3. Kabhi kabhi",
        "summary_confirm": "📝 *Yeh details sahi hai?*\n\n📍 Location: {loc}\n📏 Area: {area}\n🌾 Crop: {crop}\n🧪 Urea: {urea}\n🔥 Burning: {burning}\n\n1. Haan, sahi hai\n2. Location badlo\n3. Shuru se karo",
        "processing": "Shukriya! 🛰️ Main abhi aapke khet ka satellite data dekh raha hoon... thoda wait karein (30–60 sec)",
        "processing_timeout": "Satellite data analyze karne mein thoda waqt lag raha hai. Hum aapko report kuch hi der mein message karenge. Dhanyawad! 🙏",
        "expert_cta": "Kya aap chahte hain ki hamare ek carbon expert aapse baat karein? Bilkul free hai.\n1. Haan, call karwao\n2. Abhi nahi",
        "expert_confirmed": "Theek hai! Aapka reference number hai: *{code}*. Expert call ke waqt ye share karein. 🙏",
        "finish": "Shukriya! Aapka carbon status update ho gaya hai. Agle season phir milenge! 🌱"
    },
    "english": {
        "welcome": "Welcome to Carbon_kheth! 🌱 Please select your language 👇\n\n1. Hinglish\n2. English\n3. हिंदी (Hindi)",
        "greeting": "Hello! 🙏 I can calculate your farm's carbon score and show you how much you can earn from carbon credits. It takes just 2 minutes.\n\nShall we start?\n1. Yes, let's start\n2. Tell me more first",
        "about": "Carbon credits pay farmers for sustainable practices like not burning stubble. We use satellite data to verify your score.",
        "location_prompt": "First, please share your farm's location 📍 (Tap the paperclip 📎 icon below -> Location -> 'Share Current Location'). Please be at your farm when sharing.",
        "location_confirm": "📍 We noted: {name} — is this correct?\n1. Yes\n2. No, change it",
        "area_prompt": "What is the total area of your farm? (You can reply in acres, hectares, or bigha)\n\nOr use this link for accuracy: {link}",
        "area_retry": "Sorry, I didn't get that. Please specify the area (e.g., 5 acres or 2.5 hectares).",
        "crop_prompt": "What are you growing this season?\n1. Wheat\n2. Paddy\n3. Maize\n4. Something else",
        "urea_prompt": "How many bags of Urea do you use per season?\n1. 0-2 bags\n2. 3-5 bags\n3. 6-10 bags\n4. 10+ bags",
        "burning_prompt": "Do you burn crop residue after harvest?\n1. Yes\n2. No\n3. Sometimes",
        "summary_confirm": "📝 *Are these details correct?*\n\n📍 Location: {loc}\n📏 Area: {area}\n🌾 Crop: {crop}\n🧪 Urea: {urea}\n🔥 Burning: {burning}\n\n1. Yes, they are correct\n2. Change location\n3. Start over",
        "processing": "Thank you! 🛰️ I am analyzing your satellite data now... please wait (30-60 sec)",
        "processing_timeout": "The satellite analysis is taking a bit longer. We will message you the report shortly. Thank you! 🙏",
        "expert_cta": "Would you like one of our agronomy experts to call you? It's completely free.\n1. Yes, please call\n2. Not right now",
        "expert_confirmed": "Great! Your reference number is: *{code}*. Please share this when our expert calls. 🙏",
        "finish": "Thank you! Your carbon status has been updated. See you next season! 🌱"
    },
    "hindi": {
        "welcome": "कार्बन_खेत (Carbon_kheth) में आपका स्वागत है! 🌱 कृपया अपनी भाषा चुनें 👇\n\n1. Hinglish\n2. English\n3. हिंदी (Hindi)",
        "greeting": "नमस्ते! 🙏 मैं आपके खेत का कार्बन स्कोर निकाल सकता हूं — और बताऊंगा कि आप कार्बन क्रेडिट से कितना कमा सकते हैं। सिर्फ 2 मिनट लगेंगे।\n\nशुरू करें?\n1. हां, शुरू करो\n2. पहले बताओ क्या है ये",
        "about": "कार्बन क्रेडिट किसानों को उनकी अच्छी प्रथाओं (जैसे पराली न जलाना) के लिए भुगतान करते हैं। हम उपग्रह से आपका स्कोर चेक करते हैं।",
        "location_prompt": "पहले अपने खेत की लोकेशन साझा करें 📍 (नीचे पेपरक्लिप 📎 आइकन दबाएं -> लोकेशन -> 'अपनी वर्तमान लोकेशन साझा करें')। कृपया लोकेशन अपने खेत से ही साझा करें।",
        "location_confirm": "📍 हमने नोट किया: {name} — क्या यह सही है?\n1. हां\n2. नहीं, बदलें",
        "area_prompt": "आपके खेत का क्षेत्रफल कितना है? (बीघा, एकड़ या हेक्टेयर में बता सकते हैं)\n\nसटीक परिणाम के लिए इस लिंक का उपयोग करें: {link}",
        "area_retry": "समझ नहीं आया 😅 कृपया क्षेत्रफल सही से लिखें (जैसे: 5 एकड़ या 2.5 हेक्टेयर)।",
        "crop_prompt": "इस मौसम में आप क्या उगा रहे हैं?\n1. गेहूं\n2. धान\n3. मक्का\n4. कुछ और",
        "urea_prompt": "एक सीजन में आप कितने बैग यूरिया का उपयोग करते हैं?\n1. 0-2 बैग\n2. 3-5 बैग\n3. 6-10 बैग\n4. 10+ बैग",
        "burning_prompt": "क्या आप फसल काटने के बाद पराली जलाते हैं?\n1. हां\n2. नहीं\n3. कभी-कभी",
        "summary_confirm": "📝 *क्या ये विवरण सही हैं?*\n\n📍 स्थान: {loc}\n📏 क्षेत्रफल: {area}\n🌾 फसल: {crop}\n🧪 यूरिया: {urea}\n🔥 पराली जलाना: {burning}\n\n1. हां, सही हैं\n2. स्थान बदलें\n3. फिर से शुरू करें",
        "processing": "शुक्रिया! 🛰️ मैं अभी आपके खेत का सैटेलाइट डेटा देख रहा हूं... थोड़ा इंतज़ार करें (30–60 सेकंड)",
        "processing_timeout": "सैटेलाइट विश्लेषण में थोड़ा समय लग रहा है। हम आपको जल्द ही रिपोर्ट भेजेंगे। धन्यवाद! 🙏",
        "expert_cta": "क्या आप चाहते हैं कि हमारे एक कृषि विशेषज्ञ आपसे बात करें? यह बिल्कुल मुफ्त है।\n1. हां, कॉल करवाओ\n2. अभी नहीं",
        "expert_confirmed": "बहुत अच्छा! आपका संदर्भ नंबर है: *{code}*। कृपया विशेषज्ञ के कॉल करने पर इसे साझा करें। 🙏",
        "finish": "धन्यवाद! आपके कार्बन की स्थिति अपडेट कर दी गई है। अगले सीजन में फिर मिलेंगे! 🌱"
    }
}

def get_text(key: str, lang: str = "hinglish", **kwargs) -> str:
    """Fetch localized text by key and language."""
    # Default to hinglish if language selection was never made or invalid
    if lang not in MESSAGES:
        lang = "hinglish"
    
    template = MESSAGES[lang].get(key, MESSAGES["hinglish"].get(key, f"[{key}]"))
    return template.format(**kwargs)
