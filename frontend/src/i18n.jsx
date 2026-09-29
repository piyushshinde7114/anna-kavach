import { createContext, useContext, useEffect, useState } from 'react'

const HI = {
  'New spec': 'नया पैक', 'My packs': 'मेरे पैक', 'Library': 'लाइब्रेरी', 'Trace a pack': 'पैक जाँचें', 'Admin': 'एडमिन',
  'hero.title': 'पैक अंदाज़े से नहीं, हिसाब से।',
  'hero.lede': 'बताइए क्या पैक कर रहे हैं और कहाँ भेज रहे हैं। अन्न कवच सफ़र का मौसम देखकर हिसाब लगाता है कि खाने को कितनी सुरक्षा चाहिए, फिर वही पैक बताता है जो सस्ता, टिकाऊ और कारगर हो।',
  'ask.placeholder': 'जैसे: 200 ग्राम केला चिप्स 6 महीने कोच्चि से दिल्ली',
  'Compute': 'हिसाब लगाएँ', 'Try': 'आज़माएँ', 'Speak': 'बोलें',
  'What do you pack?': 'आप क्या पैक करते हैं?', 'Pack and shelf life': 'पैक और शेल्फ़ लाइफ़', 'Journey': 'सफ़र',
  'Pack weight (g)': 'पैक वज़न (ग्राम)', 'Pouch width (cm)': 'पाउच चौड़ाई (सेमी)', 'Pouch height (cm)': 'पाउच ऊँचाई (सेमी)',
  'Target shelf life (days)': 'चाहिए शेल्फ़ लाइफ़ (दिन)', 'Fill per bag (kg)': 'एक बैग में (किलो)',
  'Packed at': 'कहाँ पैक होता है', 'Sold in': 'कहाँ बिकता है', 'Dispatch month': 'भेजने का महीना', 'Transport': 'परिवहन',
  'Reefer truck': 'रीफ़र (ठंडा) ट्रक', 'Ambient truck': 'साधारण ट्रक', 'Rail': 'रेल', 'Hours at retail': 'दुकान पर घंटे',
  'Design my pack': 'मेरा पैक बनाइए', 'Working it out': 'हिसाब चल रहा है',
  'Not in the list? Describe it': 'सूची में नहीं? बनावट बताइए',
  'Three packs that pass': 'तीन पैक जो पास हैं', 'What the food needs': 'खाने को क्या चाहिए',
  'Download spec sheet (PDF)': 'स्पेक शीट (PDF)', 'Open trace page': 'ट्रेस पेज खोलें',
  'Report real shelf life': 'असली शेल्फ़ लाइफ़ बताइए',
}

const Ctx = createContext({ lang: 'en', t: (k) => k, setLang: () => {} })
export function I18n({ children }) {
  const [lang, setLang] = useState(() => { try { return localStorage.getItem('ak-lang') || 'en' } catch { return 'en' } })
  useEffect(() => { try { localStorage.setItem('ak-lang', lang) } catch {} ; document.documentElement.lang = lang === 'hi' ? 'hi' : 'en' }, [lang])
  const EN = {
    'hero.title': 'Packs worked out, not guessed.',
    'hero.lede': 'Tell us what you pack and where it travels. Anna Kavach reads the weather on that route, works out how much protection the food needs, and hands you the pack that delivers it for the least money and plastic.',
    'ask.placeholder': 'e.g. 200 g banana chips, 6 months, Kochi to Delhi',
  }
  const t = (k) => (lang === 'hi' ? HI[k] : EN[k]) || EN[k] || k
  return <Ctx.Provider value={{ lang, setLang, t }}>{children}</Ctx.Provider>
}
export const useT = () => useContext(Ctx)
