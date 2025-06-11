import requests
import logging
import openai
from typing import Dict, Any, Tuple, List, Optional
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Common drug name mappings
DRUG_MAPPINGS = {
    # Pain relievers
    'tylenol': 'acetaminophen',
    'advil': 'ibuprofen',
    'motrin': 'ibuprofen',
    'aleve': 'naproxen',
    'aspirin': 'acetylsalicylic acid',
    'excedrin': 'acetaminophen aspirin caffeine',
    
    # Antihistamines
    'zyrtec': 'cetirizine',
    'claritin': 'loratadine',
    'allegra': 'fexofenadine',
    'benadryl': 'diphenhydramine',
    
    # Antibiotics
    'amoxicillin': 'amoxicillin',
    'penicillin': 'penicillin',
    'azithromycin': 'azithromycin',
    'doxycycline': 'doxycycline',
    
    # Blood pressure
    'lisinopril': 'lisinopril',
    'amlodipine': 'amlodipine',
    'metoprolol': 'metoprolol',
    
    # Cholesterol
    'lipitor': 'atorvastatin',
    'zocor': 'simvastatin',
    'crestor': 'rosuvastatin',
    
    # Diabetes
    'metformin': 'metformin',
    'glucophage': 'metformin',
    'insulin': 'insulin',
    
    # Mental health
    'zoloft': 'sertraline',
    'prozac': 'fluoxetine',
    'lexapro': 'escitalopram',
    'celexa': 'citalopram',
    
    # Sleep aids
    'ambien': 'zolpidem',
    'lunesta': 'eszopiclone',
    'melatonin': 'melatonin',
    
    # Supplements
    'cbd': 'cannabidiol',
    'vitamin d': 'cholecalciferol',
    'fish oil': 'omega-3 fatty acids',
    
    # Other common substances
    'alcohol': 'ethanol',
    'beer': 'ethanol',
    'wine': 'ethanol',
    'grapefruit': 'grapefruit',
    'birth control': 'oral contraceptives',
}

# Known critical interactions
CRITICAL_INTERACTIONS = {
    ('warfarin', 'ibuprofen'): "Warfarin and ibuprofen can increase bleeding risk.",
    ('warfarin', 'aspirin'): "Warfarin and aspirin can increase bleeding risk.",
    ('warfarin', 'acetaminophen'): "High doses of acetaminophen may affect warfarin.",
    ('alcohol', 'acetaminophen'): "Alcohol and acetaminophen can cause liver damage.",
    ('alcohol', 'ibuprofen'): "Alcohol and ibuprofen can increase stomach bleeding risk.",
    ('alcohol', 'aspirin'): "Alcohol and aspirin can increase stomach bleeding risk.",
    ('alcohol', 'metformin'): "Alcohol can increase the risk of lactic acidosis with metformin.",
    ('grapefruit', 'simvastatin'): "Grapefruit can increase simvastatin levels in blood.",
    ('grapefruit', 'atorvastatin'): "Grapefruit can increase atorvastatin levels in blood.",
    ('grapefruit', 'amlodipine'): "Grapefruit can increase amlodipine levels in blood.",
    ('antibiotics', 'birth control'): "Some antibiotics may reduce birth control effectiveness.",
    ('cbd', 'warfarin'): "CBD may increase warfarin's blood-thinning effects.",
    ('cbd', 'clobazam'): "CBD may increase clobazam levels in blood.",
    ('melatonin', 'anticoagulants'): "Melatonin may increase bleeding risk with blood thinners.",
    ('melatonin', 'antidepressants'): "Melatonin may interact with some antidepressants.",
}

# Add at the top of the file, after imports
COMMON_DRUG_INFO = {
    'sertraline': {
        'description': 'Sertraline is an antidepressant medication used to treat depression, anxiety disorders, panic attacks, and obsessive-compulsive disorder (OCD).',
        'side_effects': 'Common side effects include: nausea, diarrhea, insomnia, dizziness, drowsiness, dry mouth, fatigue, sweating, and sexual problems. Serious side effects may include: suicidal thoughts, serotonin syndrome, and bleeding problems.',
        'warnings': 'WARNING: Sertraline may increase the risk of suicidal thoughts and behavior in children, adolescents, and young adults. Monitor for worsening depression or unusual changes in behavior.',
        'precautions': 'Do not use if you are taking MAO inhibitors or have taken them in the past 14 days. Tell your doctor if you have: liver problems, kidney problems, seizures, bipolar disorder, or if you are pregnant or breastfeeding.',
        'interactions': {
            'ibuprofen': 'CAUTION: Taking sertraline with ibuprofen may increase the risk of bleeding. Monitor for unusual bruising or bleeding.',
            'melatonin': 'CAUTION: Taking sertraline with melatonin may increase drowsiness and dizziness. Use caution when driving or operating machinery.',
            'alcohol': 'WARNING: Drinking alcohol while taking sertraline can increase drowsiness and dizziness. Avoid or limit alcohol consumption.'
        }
    },
    'melatonin': {
        'description': 'Melatonin is a hormone that helps regulate sleep-wake cycles. It is used to treat insomnia and sleep disorders.',
        'side_effects': 'Common side effects include: drowsiness, headache, dizziness, nausea. Serious side effects are rare but may include: confusion, depression, and low blood pressure.',
        'warnings': 'WARNING: Do not drive or operate machinery after taking melatonin. May cause drowsiness.',
        'precautions': 'Do not use if you are pregnant or breastfeeding. Tell your doctor if you have: depression, bleeding disorders, or if you are taking blood thinners.',
        'interactions': {
            'sertraline': 'CAUTION: Taking melatonin with sertraline may increase drowsiness and dizziness. Use caution when driving or operating machinery.',
            'blood_thinners': 'CAUTION: Melatonin may increase the risk of bleeding when taken with blood thinners.',
            'alcohol': 'CAUTION: Taking melatonin with alcohol may increase drowsiness.'
        }
    },
    'ibuprofen': {
        'description': 'Ibuprofen is a nonsteroidal anti-inflammatory drug (NSAID) used to reduce fever and treat pain or inflammation caused by many conditions such as headache, toothache, back pain, arthritis, menstrual cramps, or minor injury.',
        'side_effects': 'Common side effects include: stomach pain, heartburn, nausea, vomiting, gas, constipation, diarrhea, dizziness, nervousness, ringing in the ears. Serious side effects may include: stomach bleeding, kidney problems, high blood pressure, heart problems, allergic reactions.',
        'warnings': 'WARNING: This product contains an NSAID, which may cause severe stomach bleeding. The chance is higher if you: take more or for a longer time than directed, take a blood thinning (anticoagulant) or steroid drug, have had stomach ulcers or bleeding problems, are over 60 years of age, have 3 or more alcoholic drinks every day while using this product.',
        'precautions': 'Do not use if you have ever had an allergic reaction to any other pain reliever/fever reducer. Ask a doctor before use if you have: problems or serious side effects from taking pain relievers or fever reducers, stomach problems that last or come back, high blood pressure, heart disease, liver cirrhosis, kidney disease, asthma, or if you are taking a diuretic.',
        'interactions': {
            'sertraline': 'CAUTION: Taking ibuprofen with sertraline may increase the risk of bleeding. Monitor for unusual bruising or bleeding.',
            'blood_thinners': 'WARNING: Taking ibuprofen with blood thinners can increase your risk of bleeding.',
            'alcohol': 'WARNING: Drinking alcohol while taking ibuprofen can increase your risk of stomach bleeding and liver damage. Limit alcohol consumption.'
        }
    },
    'acetaminophen': {
        'description': 'Acetaminophen is a pain reliever and fever reducer used to treat many conditions such as headache, muscle aches, arthritis, backache, toothaches, colds, and fevers.',
        'side_effects': 'Common side effects are rare but may include: allergic reactions, skin rash, hives, itching, swelling of the face, throat, tongue, lips, eyes, hands, feet, ankles, or lower legs, hoarseness, difficulty breathing or swallowing.',
        'warnings': 'WARNING: Taking more than the recommended dose may cause liver damage. Do not take with other products containing acetaminophen. Ask a doctor before use if you have liver disease.',
        'precautions': 'Do not use if you are allergic to acetaminophen or any of the inactive ingredients. Ask a doctor before use if you have liver disease. Stop use and ask a doctor if pain gets worse or lasts more than 10 days, fever gets worse or lasts more than 3 days, or new symptoms occur.'
    },
    'metformin': {
        'description': 'Metformin is an oral diabetes medicine that helps control blood sugar levels. It is used together with diet and exercise to improve blood sugar control in adults with type 2 diabetes mellitus.',
        'side_effects': 'Common side effects include: nausea, vomiting, stomach upset, diarrhea, weakness, or a metallic taste in the mouth. Serious side effects may include: lactic acidosis (rare but serious), vitamin B12 deficiency, low blood sugar (when used with other diabetes medications).',
        'warnings': 'WARNING: Lactic acidosis is a rare but serious side effect that can be fatal. Stop taking metformin and get medical help right away if you have symptoms of lactic acidosis: unusual muscle pain, trouble breathing, stomach pain, dizziness, feeling cold, or feeling very weak or tired.',
        'precautions': 'Do not use if you have severe kidney disease or are on dialysis. Tell your doctor if you have: kidney problems, liver disease, heart failure, or if you are over 80 years old. Avoid drinking large amounts of alcohol while taking metformin.',
        'interactions': {
            'alcohol': 'WARNING: Drinking alcohol while taking metformin can increase the risk of lactic acidosis, a serious and potentially fatal condition. Avoid or limit alcohol consumption.',
            'insulin': 'CAUTION: Taking metformin with insulin can increase the risk of low blood sugar. Monitor blood sugar levels closely.',
            'iodinated_contrast': 'WARNING: Metformin should be temporarily stopped before and after procedures using iodinated contrast media.',
            'topiramate': 'CAUTION: May increase the risk of lactic acidosis.',
            'cimetidine': 'CAUTION: May increase metformin levels in the blood.'
        }
    },
    'aspirin': {
        'description': 'Aspirin is a salicylate (sa-LIS-il-ate) used to treat pain, and reduce fever or inflammation. It is sometimes used to treat or prevent heart attacks, strokes, and chest pain (angina).',
        'side_effects': 'Common side effects include: upset stomach, heartburn, drowsiness, mild headache. Serious side effects may include: severe stomach pain, black/tarry stools, vomit that looks like coffee grounds, ringing in the ears, hearing loss, confusion, hallucinations, rapid breathing, seizure.',
        'warnings': 'WARNING: This product contains an NSAID, which may cause severe stomach bleeding. The chance is higher if you: take more or for a longer time than directed, take a blood thinning (anticoagulant) or steroid drug, have had stomach ulcers or bleeding problems, are over 60 years of age, have 3 or more alcoholic drinks every day while using this product.',
        'precautions': 'Do not use if you have: a history of stomach ulcers or bleeding problems, asthma, nasal polyps, bleeding disorders, or if you are allergic to aspirin or other NSAIDs. Ask a doctor before use if you have: heart disease, high blood pressure, liver cirrhosis, or kidney disease.'
    },
    'amoxicillin': {
        'description': 'Amoxicillin is a penicillin antibiotic that fights bacteria in the body. It is used to treat many different types of infection caused by bacteria, such as tonsillitis, bronchitis, pneumonia, and infections of the ear, nose, throat, skin, or urinary tract.',
        'side_effects': 'Common side effects include: diarrhea, nausea, vomiting, stomach pain, headache, rash, or vaginal itching. Serious side effects may include: severe allergic reactions, severe diarrhea, yellowing of the skin or eyes, dark urine, or unusual bleeding or bruising.',
        'warnings': 'WARNING: This medication may cause severe allergic reactions. Stop taking amoxicillin and get emergency medical help if you have: hives, difficulty breathing, swelling of your face, lips, tongue, or throat.',
        'precautions': 'Do not use if you are allergic to amoxicillin or to any other penicillin antibiotic. Tell your doctor if you have: kidney disease, mononucleosis, or if you are pregnant or breastfeeding.'
    },
    'insulin': {
        'description': 'Insulin is a hormone that helps control blood sugar levels. It is used to treat diabetes by helping glucose enter cells to be used for energy.',
        'side_effects': 'Common side effects include: weight gain, low blood sugar (hypoglycemia), injection site reactions. Serious side effects may include: severe allergic reactions, severe low blood sugar, heart failure.',
        'warnings': 'WARNING: Insulin can cause low blood sugar, which can be life-threatening. Symptoms include: sweating, confusion, dizziness, hunger, fast heartbeat, shaking, or feeling nervous.',
        'precautions': 'Do not use if you are allergic to insulin or any of its ingredients. Tell your doctor if you have: kidney or liver problems, heart failure, or if you are pregnant or breastfeeding.',
        'interactions': {
            'alcohol': 'WARNING: Drinking alcohol while taking insulin can increase the risk of low blood sugar. Monitor blood sugar levels closely and limit alcohol consumption.',
            'corticosteroids': 'CAUTION: May increase blood sugar levels, requiring insulin dose adjustment.',
            'beta_blockers': 'CAUTION: May mask symptoms of low blood sugar.',
            'thiazolidinediones': 'CAUTION: May increase the risk of heart failure.',
            'metformin': 'CAUTION: Taking insulin with metformin can increase the risk of low blood sugar. Monitor blood sugar levels closely.'
        }
    },
    'amlodipine': {
        'description': 'Amlodipine is a calcium channel blocker used to treat high blood pressure and chest pain (angina).',
        'side_effects': 'Common side effects include: headache, swelling in the ankles or feet, dizziness, flushing, fatigue. Serious side effects may include: severe dizziness, fainting, fast/irregular heartbeat, severe stomach/abdominal pain.',
        'warnings': 'WARNING: Amlodipine may cause a serious drop in blood pressure. Get up slowly when rising from a sitting or lying position.',
        'precautions': 'Tell your doctor if you have: liver disease, heart failure, or if you are pregnant or breastfeeding.',
        'interactions': {
            'simvastatin': 'CAUTION: Taking amlodipine with simvastatin may increase the risk of muscle pain and weakness. Monitor for muscle pain.',
            'grapefruit': 'WARNING: Grapefruit and grapefruit juice may increase the amount of amlodipine in your blood, which could increase side effects.',
            'alcohol': 'CAUTION: Drinking alcohol while taking amlodipine may increase dizziness and drowsiness.'
        }
    },
    'simvastatin': {
        'description': 'Simvastatin is a statin medication used to lower cholesterol and reduce the risk of heart disease.',
        'side_effects': 'Common side effects include: headache, nausea, stomach pain, constipation, muscle pain. Serious side effects may include: muscle problems, liver problems, memory problems.',
        'warnings': 'WARNING: Simvastatin may cause serious muscle problems that can lead to kidney failure. Contact your doctor if you have unexplained muscle pain, tenderness, or weakness.',
        'precautions': 'Do not use if you are pregnant or breastfeeding. Tell your doctor if you have: liver disease, kidney disease, or if you drink more than 2 alcoholic beverages daily.',
        'interactions': {
            'amlodipine': 'CAUTION: Taking simvastatin with amlodipine may increase the risk of muscle pain and weakness. Monitor for muscle pain.',
            'grapefruit': 'WARNING: Grapefruit and grapefruit juice may increase the amount of simvastatin in your blood, which could increase side effects.',
            'alcohol': 'CAUTION: Drinking alcohol while taking simvastatin may increase the risk of liver problems.'
        }
    },
    'grapefruit': {
        'description': 'Grapefruit and grapefruit juice can interact with many medications by affecting how they are metabolized in the body.',
        'side_effects': 'Grapefruit itself is generally safe, but it can cause serious interactions with certain medications.',
        'warnings': 'WARNING: Grapefruit and grapefruit juice can interact with many medications, potentially causing serious side effects.',
        'precautions': 'Avoid grapefruit and grapefruit juice if you are taking medications that interact with it. Check with your healthcare provider.',
        'interactions': {
            'amlodipine': 'WARNING: Grapefruit may increase the amount of amlodipine in your blood, which could increase side effects.',
            'simvastatin': 'WARNING: Grapefruit may increase the amount of simvastatin in your blood, which could increase side effects.',
            'alcohol': 'No significant interaction'
        }
    },
    'atorvastatin': {
        'description': 'Atorvastatin is a statin medication used to lower cholesterol and reduce the risk of heart disease.',
        'side_effects': 'Common side effects include: muscle pain, diarrhea, joint pain, insomnia, and stuffy nose. Serious side effects may include: liver problems, muscle breakdown, and memory problems.',
        'warnings': 'WARNING: Atorvastatin may cause serious muscle problems that can lead to kidney failure. Contact your doctor if you have unexplained muscle pain, tenderness, or weakness.',
        'precautions': 'Do not use if you are pregnant or breastfeeding. Tell your doctor if you have: liver disease, kidney disease, or if you drink more than 2 alcoholic beverages daily.',
        'interactions': {
            'birth_control': 'CAUTION: Atorvastatin may reduce the effectiveness of birth control pills. Use additional contraception.',
            'antibiotics': 'CAUTION: Some antibiotics may increase the risk of muscle problems when taken with atorvastatin.',
            'grapefruit': 'WARNING: Grapefruit and grapefruit juice may increase the amount of atorvastatin in your blood.',
            'alcohol': 'CAUTION: Drinking alcohol while taking atorvastatin may increase the risk of liver problems.'
        }
    },
    'amoxicillin': {
        'description': 'Amoxicillin is an antibiotic used to treat bacterial infections.',
        'side_effects': 'Common side effects include: diarrhea, nausea, vomiting, and rash. Serious side effects may include: severe allergic reactions, liver problems, and severe diarrhea.',
        'warnings': 'WARNING: Stop taking amoxicillin and get emergency help if you have signs of an allergic reaction: hives, difficulty breathing, swelling of face/lips/tongue.',
        'precautions': 'Tell your doctor if you have: kidney disease, mononucleosis, or if you are pregnant or breastfeeding.',
        'interactions': {
            'birth_control': 'CAUTION: Amoxicillin may reduce the effectiveness of birth control pills. Use additional contraception.',
            'alcohol': 'CAUTION: Drinking alcohol while taking amoxicillin may reduce its effectiveness and increase side effects.'
        }
    },
    'warfarin': {
        'description': 'Warfarin is an anticoagulant (blood thinner) used to prevent blood clots.',
        'side_effects': 'Common side effects include: bleeding, bruising, and stomach pain. Serious side effects may include: severe bleeding, stroke, and gangrene.',
        'warnings': 'WARNING: Warfarin can cause serious or fatal bleeding. Regular blood tests are required to monitor its effects.',
        'precautions': 'Tell your doctor if you have: bleeding problems, recent surgery, or if you are pregnant or breastfeeding.',
        'interactions': {
            'ibuprofen': 'WARNING: Taking ibuprofen with warfarin can increase the risk of bleeding.',
            'alcohol': 'WARNING: Drinking alcohol while taking warfarin can increase the risk of bleeding.',
            'grapefruit': 'CAUTION: Grapefruit may affect how warfarin works in your body.'
        }
    },
    'cetirizine': {
        'description': 'Cetirizine is an antihistamine used to treat allergy symptoms.',
        'side_effects': 'Common side effects include: drowsiness, dry mouth, and fatigue. Serious side effects are rare but may include: severe allergic reactions.',
        'warnings': 'WARNING: Cetirizine may cause drowsiness. Do not drive or operate machinery until you know how it affects you.',
        'precautions': 'Tell your doctor if you have: kidney disease, liver disease, or if you are pregnant or breastfeeding.',
        'interactions': {
            'loratadine': 'CAUTION: Taking cetirizine with loratadine may increase side effects. Use only one antihistamine at a time.',
            'alcohol': 'CAUTION: Drinking alcohol while taking cetirizine may increase drowsiness.'
        }
    },
    'loratadine': {
        'description': 'Loratadine is an antihistamine used to treat allergy symptoms.',
        'side_effects': 'Common side effects include: headache, drowsiness, and dry mouth. Serious side effects are rare but may include: severe allergic reactions.',
        'warnings': 'WARNING: Loratadine may cause drowsiness. Do not drive or operate machinery until you know how it affects you.',
        'precautions': 'Tell your doctor if you have: liver disease, kidney disease, or if you are pregnant or breastfeeding.',
        'interactions': {
            'cetirizine': 'CAUTION: Taking loratadine with cetirizine may increase side effects. Use only one antihistamine at a time.',
            'alcohol': 'CAUTION: Drinking alcohol while taking loratadine may increase drowsiness.'
        }
    },
    'naproxen': {
        'description': 'Naproxen is a nonsteroidal anti-inflammatory drug (NSAID) used to treat pain and inflammation.',
        'side_effects': 'Common side effects include: stomach pain, heartburn, and dizziness. Serious side effects may include: stomach bleeding, kidney problems, and heart problems.',
        'warnings': 'WARNING: Naproxen may increase the risk of heart attack, stroke, and stomach bleeding.',
        'precautions': 'Do not use if you have: heart disease, stomach ulcers, or if you are pregnant or breastfeeding.',
        'interactions': {
            'ibuprofen': 'WARNING: Taking naproxen with ibuprofen may increase the risk of side effects. Use only one NSAID at a time.',
            'aspirin': 'WARNING: Taking naproxen with aspirin may increase the risk of stomach bleeding.',
            'alcohol': 'WARNING: Drinking alcohol while taking naproxen may increase the risk of stomach bleeding.'
        }
    },
    'cbd': {
        'description': 'CBD (cannabidiol) is a compound from the cannabis plant used for various conditions.',
        'side_effects': 'Common side effects include: drowsiness, dry mouth, and changes in appetite. Serious side effects are rare but may include: liver problems.',
        'warnings': 'WARNING: CBD may interact with many medications. Consult your healthcare provider before use.',
        'precautions': 'Tell your doctor if you are taking any medications, especially blood thinners or seizure medications.',
        'interactions': {
            'blood_thinners': 'WARNING: CBD may increase the effects of blood thinners, increasing the risk of bleeding.',
            'blood_pressure_meds': 'CAUTION: CBD may lower blood pressure, which could be dangerous when taken with blood pressure medications.'
        }
    },
    'birth_control': {
        'description': 'Birth control pills are hormonal contraceptives used to prevent pregnancy.',
        'side_effects': 'Common side effects include: nausea, breast tenderness, and irregular bleeding. Serious side effects may include: blood clots, stroke, and heart attack.',
        'warnings': 'WARNING: Birth control pills may increase the risk of blood clots, especially in women who smoke or are over 35.',
        'precautions': 'Do not use if you have: blood clots, heart disease, or if you are pregnant or breastfeeding.',
        'interactions': {
            'antibiotics': 'CAUTION: Some antibiotics may reduce the effectiveness of birth control pills. Use additional contraception.',
            'atorvastatin': 'CAUTION: Atorvastatin may reduce the effectiveness of birth control pills. Use additional contraception.'
        }
    },
    'antibiotics': {
        'description': 'Antibiotics are medications used to treat bacterial infections.',
        'side_effects': 'Common side effects include: diarrhea, nausea, and allergic reactions. Serious side effects may include: severe allergic reactions and antibiotic-resistant infections.',
        'warnings': 'WARNING: Take antibiotics exactly as prescribed. Do not stop early or share with others.',
        'precautions': 'Tell your doctor if you have: kidney disease, liver disease, or if you are pregnant or breastfeeding.',
        'interactions': {
            'birth_control': 'CAUTION: Some antibiotics may reduce the effectiveness of birth control pills. Use additional contraception.',
            'alcohol': 'CAUTION: Drinking alcohol while taking antibiotics may reduce their effectiveness and increase side effects.'
        }
    },
    'mao_inhibitors': {
        'description': 'MAO inhibitors are a class of antidepressants used to treat depression.',
        'side_effects': 'Common side effects include: dizziness, drowsiness, and dry mouth. Serious side effects may include: high blood pressure crisis and serotonin syndrome.',
        'warnings': 'WARNING: MAO inhibitors can cause dangerous interactions with many foods and medications.',
        'precautions': 'Avoid foods containing tyramine and many medications. Tell your doctor about all medications you take.',
        'interactions': {
            'alcohol': 'WARNING: Drinking alcohol while taking MAO inhibitors can cause dangerous high blood pressure.',
            'sertraline': 'WARNING: Taking sertraline with MAO inhibitors can cause serotonin syndrome.'
        }
    },
    'blood_thinners': {
        'description': 'Blood thinners are medications used to prevent blood clots.',
        'side_effects': 'Common side effects include: bleeding, bruising, and stomach pain. Serious side effects may include: severe bleeding and stroke.',
        'warnings': 'WARNING: Blood thinners can cause serious or fatal bleeding. Regular blood tests may be required.',
        'precautions': 'Tell your doctor if you have: bleeding problems, recent surgery, or if you are pregnant or breastfeeding.',
        'interactions': {
            'ibuprofen': 'WARNING: Taking ibuprofen with blood thinners can increase the risk of bleeding.',
            'alcohol': 'WARNING: Drinking alcohol while taking blood thinners can increase the risk of bleeding.'
        }
    },
    'blood_pressure_meds': {
        'description': 'Blood pressure medications are used to treat high blood pressure.',
        'side_effects': 'Common side effects include: dizziness, fatigue, and cough. Serious side effects may include: low blood pressure and kidney problems.',
        'warnings': 'WARNING: Blood pressure medications can cause dangerously low blood pressure if taken with certain medications.',
        'precautions': 'Tell your doctor if you have: kidney disease, heart disease, or if you are pregnant or breastfeeding.',
        'interactions': {
            'alcohol': 'WARNING: Drinking alcohol while taking blood pressure medications can cause dangerously low blood pressure.',
            'cbd': 'CAUTION: CBD may lower blood pressure, which could be dangerous when taken with blood pressure medications.'
        }
    },
    'metoprolol': {
        'description': 'Metoprolol is a beta-blocker used to treat high blood pressure and heart conditions.',
        'side_effects': 'Common side effects include: dizziness, fatigue, and depression. Serious side effects may include: heart failure and severe allergic reactions.',
        'warnings': 'WARNING: Do not stop taking metoprolol suddenly as this may cause serious heart problems.',
        'precautions': 'Tell your doctor if you have: heart failure, asthma, or if you are pregnant or breastfeeding.',
        'interactions': {
            'alcohol': 'WARNING: Drinking alcohol while taking metoprolol can cause dangerously low blood pressure.',
            'cbd': 'CAUTION: CBD may lower blood pressure, which could be dangerous when taken with metoprolol.'
        }
    },
    'dementia_meds': {
        'description': 'Dementia medications are used to treat symptoms of dementia and Alzheimer\'s disease.',
        'side_effects': 'Common side effects include: nausea, vomiting, and diarrhea. Serious side effects may include: heart problems and severe allergic reactions.',
        'warnings': 'WARNING: Dementia medications can cause serious side effects in people with certain heart conditions.',
        'precautions': 'Tell your doctor if you have: heart disease, asthma, or if you are pregnant or breastfeeding.',
        'interactions': {
            'blood_pressure_meds': 'CAUTION: Taking dementia medications with blood pressure medications may increase side effects.',
            'alcohol': 'WARNING: Drinking alcohol while taking dementia medications can increase side effects.'
        }
    }
}

def normalize_drug_name(drug_name: str) -> str:
    """Normalize drug name to standard form"""
    if not drug_name or not isinstance(drug_name, str):
        return ''
        
    drug_name = drug_name.lower().strip()
    
    # Strict list of known drugs and their variations
    drug_mappings = {
        'sertraline': 'sertraline',
        'zoloft': 'sertraline',
        'melatonin': 'melatonin',
        'ibuprofen': 'ibuprofen',
        'advil': 'ibuprofen',
        'motrin': 'ibuprofen',
        'brufen': 'ibuprofen',
        'nurofen': 'ibuprofen',
        'metformin': 'metformin',
        'glucophage': 'metformin',
        'insulin': 'insulin',
        'alcohol': 'alcohol',
        'ethanol': 'alcohol',
        'drinking': 'alcohol',
        'beer': 'alcohol',
        'wine': 'alcohol',
        'liquor': 'alcohol',
        'drink': 'alcohol',
        'drinks': 'alcohol',
        'alcoholic': 'alcohol',
        'alcoholic beverage': 'alcohol',
        'alcoholic beverages': 'alcohol',
        'aspirin': 'aspirin',
        'bayer': 'aspirin',
        'bufferin': 'aspirin',
        'ecotrin': 'aspirin',
        'acetaminophen': 'acetaminophen',
        'tylenol': 'acetaminophen',
        'paracetamol': 'acetaminophen',
        'panadol': 'acetaminophen',
        'amlodipine': 'amlodipine',
        'norvasc': 'amlodipine',
        'simvastatin': 'simvastatin',
        'zocor': 'simvastatin',
        'grapefruit': 'grapefruit',
        'grapefruit juice': 'grapefruit',
        'atorvastatin': 'atorvastatin',
        'lipitor': 'atorvastatin',
        'amoxicillin': 'amoxicillin',
        'amoxil': 'amoxicillin',
        'warfarin': 'warfarin',
        'coumadin': 'warfarin',
        'cetirizine': 'cetirizine',
        'zyrtec': 'cetirizine',
        'loratadine': 'loratadine',
        'claritin': 'loratadine',
        'naproxen': 'naproxen',
        'aleve': 'naproxen',
        'cbd': 'cbd',
        'cbd oil': 'cbd',
        'cannabidiol': 'cbd',
        'birth control': 'birth_control',
        'oral contraceptive': 'birth_control',
        'contraceptive': 'birth_control',
        'birth control pills': 'birth_control',
        'the pill': 'birth_control',
        'birthcontrol': 'birth_control',
        'antibiotics': 'antibiotics',
        'antibiotic': 'antibiotics',
        'mao inhibitor': 'mao_inhibitors',
        'mao inhibitors': 'mao_inhibitors',
        'blood thinner': 'blood_thinners',
        'blood thinners': 'blood_thinners',
        'anticoagulant': 'blood_thinners',
        'anticoagulants': 'blood_thinners',
        'blood pressure medication': 'blood_pressure_meds',
        'blood pressure med': 'blood_pressure_meds',
        'blood pressure medicine': 'blood_pressure_meds',
        'metoprolol': 'metoprolol',
        'lopressor': 'metoprolol',
        'toprol': 'metoprolol',
        'dementia medication': 'dementia_meds',
        'dementia med': 'dementia_meds',
        'dementia medicine': 'dementia_meds'
    }
    
    # Only return known drugs, no guessing
    normalized = drug_mappings.get(drug_name, '')
    if normalized and normalized in COMMON_DRUG_INFO:
        return normalized
    return ''

def extract_drugs_from_query(query: str) -> List[str]:
    """Extract drug names from a natural language query"""
    if not query or not isinstance(query, str):
        return []
        
    # Convert to lowercase for consistent matching
    query = query.lower()
    
    # Strict list of known drugs and their variations
    drug_variations = {
        'sertraline': ['sertraline', 'zoloft'],
        'melatonin': ['melatonin'],
        'ibuprofen': ['ibuprofen', 'advil', 'motrin', 'brufen', 'nurofen'],
        'metformin': ['metformin', 'glucophage'],
        'insulin': ['insulin'],
        'alcohol': ['alcohol', 'ethanol', 'drinking', 'beer', 'wine', 'liquor', 'drink', 'drinks', 'alcoholic', 'alcoholic beverage', 'alcoholic beverages'],
        'aspirin': ['aspirin', 'bayer', 'bufferin', 'ecotrin'],
        'acetaminophen': ['acetaminophen', 'tylenol', 'paracetamol', 'panadol'],
        'amlodipine': ['amlodipine', 'norvasc'],
        'simvastatin': ['simvastatin', 'zocor'],
        'grapefruit': ['grapefruit', 'grapefruit juice'],
        'atorvastatin': ['atorvastatin', 'lipitor'],
        'amoxicillin': ['amoxicillin', 'amoxil'],
        'warfarin': ['warfarin', 'coumadin'],
        'cetirizine': ['cetirizine', 'zyrtec'],
        'loratadine': ['loratadine', 'claritin'],
        'naproxen': ['naproxen', 'aleve'],
        'cbd': ['cbd', 'cbd oil', 'cannabidiol'],
        'birth_control': ['birth control', 'oral contraceptive', 'contraceptive', 'birth control pills', 'the pill', 'birthcontrol'],
        'antibiotics': ['antibiotics', 'antibiotic'],
        'mao_inhibitors': ['mao inhibitor', 'mao inhibitors'],
        'blood_thinners': ['blood thinner', 'blood thinners', 'anticoagulant', 'anticoagulants'],
        'blood_pressure_meds': ['blood pressure medication', 'blood pressure med', 'blood pressure medicine'],
        'metoprolol': ['metoprolol', 'lopressor', 'toprol'],
        'dementia_meds': ['dementia medication', 'dementia med', 'dementia medicine']
    }
    
    # Extract only known drugs mentioned in the query
    found_drugs = set()
    
    # First check for exact matches
    for drug, variations in drug_variations.items():
        if any(variation in query for variation in variations):
            found_drugs.add(drug)
    
    # Handle special cases
    if 'painkiller' in query or 'pain killers' in query:
        found_drugs.update(['ibuprofen', 'acetaminophen', 'aspirin'])
    if 'antidepressant' in query or 'antidepressants' in query:
        found_drugs.add('sertraline')
    if 'antihistamine' in query or 'antihistamines' in query:
        found_drugs.update(['cetirizine', 'loratadine'])
    if 'statin' in query or 'statins' in query:
        found_drugs.update(['atorvastatin', 'simvastatin'])
    
    # Filter out empty strings and ensure drugs exist in database
    valid_drugs = [drug for drug in found_drugs if drug and drug in COMMON_DRUG_INFO]
    
    # Log the extracted drugs for debugging
    logger.info(f"Extracted drugs from query: {valid_drugs}")
    
    return valid_drugs

def get_fda_data(drug_name: str) -> Dict[str, str]:
    """Get FDA data for a drug"""
    try:
        # Normalize drug name
        normalized_name = normalize_drug_name(drug_name)
        if not normalized_name:
            raise ValueError(f"Unknown drug: {drug_name}")
        
        # Get drug info from our database
        drug_info = COMMON_DRUG_INFO.get(normalized_name)
        if not drug_info:
            raise ValueError(f"No information available for: {drug_name}")
        
        return {
            'name': drug_name,
            'info': f"{drug_info['description']}\n\nSide Effects: {drug_info['side_effects']}\n\nWarnings: {drug_info['warnings']}\n\nPrecautions: {drug_info['precautions']}",
            'side_effects': drug_info['side_effects'],
            'warnings': drug_info['warnings'],
            'precautions': drug_info['precautions'],
            'description': drug_info['description'],
            'is_safe': True
        }
    except Exception as e:
        logger.error(f"Error getting FDA data: {str(e)}")
        raise ValueError(f"Error retrieving information for {drug_name}")

def analyze_with_ai(drugs: List[str], query_type: str = "interaction") -> Tuple[bool, str]:
    """Analyze drug interactions or side effects using OpenAI API"""
    try:
        if not openai.api_key:
            return True, "Note: Advanced AI analysis is not available. Please consult your healthcare provider for detailed information."

        if query_type == "side_effects" and len(drugs) == 1:
            prompt = f"""Analyze the potential side effects of {drugs[0]}.
            Consider:
            1. Common side effects
            2. Serious side effects
            3. When to seek medical attention
            4. Special precautions
            
            Provide a clear, concise response focusing on safety."""
        else:
            prompt = f"""Analyze the potential interactions between these medications: {', '.join(drugs)}.
            Consider:
            1. Known drug interactions
            2. Timing of administration
            3. General safety recommendations
            4. When to seek medical attention
            5. Special precautions for specific populations
            
            Provide a clear, concise response focusing on safety."""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a medical information assistant. Provide clear, factual information about drug interactions and side effects. Always emphasize consulting healthcare providers for personalized advice."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )

        analysis = response.choices[0].message.content
        is_safe = "dangerous" not in analysis.lower() and "severe" not in analysis.lower()
        return is_safe, analysis

    except Exception as e:
        logger.error(f"Error in AI analysis: {str(e)}")
        return True, "Note: Advanced analysis is not available. Please consult your healthcare provider for detailed information."

def check_drug_interaction(drugs: List[str], query_type: str = "interaction") -> Tuple[bool, str]:
    """Check for interactions between multiple drugs or get side effects"""
    try:
        if len(drugs) < 1:
            return True, "Please specify at least one medication."

        # For single drug queries about side effects
        if query_type == "side_effects" and len(drugs) == 1:
            drug_info = get_fda_data(drugs[0])
            return True, f"Side effects of {drugs[0]}: {drug_info['side_effects']}"

        # For single drug queries about precautions
        if query_type == "precautions" and len(drugs) == 1:
            drug_info = get_fda_data(drugs[0])
            return True, f"Precautions for {drugs[0]}: {drug_info['precautions']}"

        # For single drug queries about warnings
        if query_type == "warnings" and len(drugs) == 1:
            drug_info = get_fda_data(drugs[0])
            return True, f"Warnings for {drugs[0]}: {drug_info['warnings']}"

        # For single drug general information
        if len(drugs) == 1:
            drug_info = get_fda_data(drugs[0])
            return True, f"Information about {drugs[0]}:\n\nDescription: {drug_info['description']}\n\nSide Effects: {drug_info['side_effects']}\n\nWarnings: {drug_info['warnings']}\n\nPrecautions: {drug_info['precautions']}"

        # For multiple drugs, check interactions
        if len(drugs) >= 2:
            interaction_messages = []
            is_safe = True
            warnings = []
            cautions = []
            
            # Check each pair of drugs
            for i, drug1 in enumerate(drugs):
                for j, drug2 in enumerate(drugs[i+1:], i+1):
                    if drug1 in COMMON_DRUG_INFO and drug2 in COMMON_DRUG_INFO:
                        interactions1 = COMMON_DRUG_INFO[drug1].get('interactions', {})
                        interactions2 = COMMON_DRUG_INFO[drug2].get('interactions', {})
                        
                        if drug2 in interactions1:
                            message = f"{drug1} and {drug2}: {interactions1[drug2]}"
                            if 'WARNING' in interactions1[drug2]:
                                warnings.append(message)
                                is_safe = False
                            else:
                                cautions.append(message)
                        elif drug1 in interactions2:
                            message = f"{drug1} and {drug2}: {interactions2[drug1]}"
                            if 'WARNING' in interactions2[drug1]:
                                warnings.append(message)
                                is_safe = False
            
            # Build response message
            response_parts = []
            
            if warnings:
                response_parts.append("WARNINGS:")
                response_parts.extend(warnings)
            
            if cautions:
                response_parts.append("\nCAUTIONS:")
                response_parts.extend(cautions)
            
            if not warnings and not cautions:
                response_parts.append("No known interactions found between these medications. However, please consult your healthcare provider before combining medications.")
            
            # Add general safety message
            response_parts.append("\n\nIMPORTANT: Always consult your healthcare provider before combining medications. This information is not a substitute for professional medical advice.")
            
            return is_safe, "\n".join(response_parts)

    except Exception as e:
        logger.error(f"Error checking drug interactions: {str(e)}")
        return True, "Unable to perform detailed analysis. Please consult your healthcare provider."

def get_drug_interaction(drug1: str, drug2: str) -> Dict[str, Any]:
    """Get interaction information between two drugs"""
    try:
        normalized_drug1 = normalize_drug_name(drug1)
        normalized_drug2 = normalize_drug_name(drug2)
        
        # Handle alcohol/ethanol as a special case
        alcohol_terms = ['alcohol', 'ethanol', 'drinking', 'beer', 'wine', 'liquor', 'drink', 'drinks', 'alcoholic', 'alcoholic beverage', 'alcoholic beverages']
        is_alcohol = normalized_drug1 in alcohol_terms or normalized_drug2 in alcohol_terms
        
        # If one of the drugs is alcohol, check interaction with the other drug
        if is_alcohol:
            other_drug = normalized_drug2 if normalized_drug1 in alcohol_terms else normalized_drug1
            if other_drug in COMMON_DRUG_INFO:
                alcohol_interaction = COMMON_DRUG_INFO[other_drug].get('interactions', {}).get('alcohol')
                if alcohol_interaction:
                    return {
                        'drug1': drug1,
                        'drug2': drug2,
                        'interaction': alcohol_interaction,
                        'severity': 'high' if 'WARNING' in alcohol_interaction else 'moderate',
                        'is_safe': False if 'WARNING' in alcohol_interaction else True,
                        'recommendation': 'Please consult your healthcare provider before consuming alcohol while taking this medication.'
                    }
        
        # Check if both drugs are in our database
        if normalized_drug1 in COMMON_DRUG_INFO and normalized_drug2 in COMMON_DRUG_INFO:
            interactions1 = COMMON_DRUG_INFO[normalized_drug1].get('interactions', {})
            interactions2 = COMMON_DRUG_INFO[normalized_drug2].get('interactions', {})
            
            # Check for direct interaction
            if normalized_drug2 in interactions1:
                return {
                    'drug1': drug1,
                    'drug2': drug2,
                    'interaction': interactions1[normalized_drug2],
                    'severity': 'high' if 'WARNING' in interactions1[normalized_drug2] else 'moderate',
                    'is_safe': False if 'WARNING' in interactions1[normalized_drug2] else True,
                    'recommendation': 'Please consult your healthcare provider before taking these medications together.'
                }
            elif normalized_drug1 in interactions2:
                return {
                    'drug1': drug1,
                    'drug2': drug2,
                    'interaction': interactions2[normalized_drug1],
                    'severity': 'high' if 'WARNING' in interactions2[normalized_drug1] else 'moderate',
                    'is_safe': False if 'WARNING' in interactions2[normalized_drug1] else True,
                    'recommendation': 'Please consult your healthcare provider before taking these medications together.'
                }
        
        # If no direct interaction found, check for common interactions
        common_interactions = []
        if normalized_drug1 in COMMON_DRUG_INFO:
            for other_drug, interaction in COMMON_DRUG_INFO[normalized_drug1].get('interactions', {}).items():
                if other_drug in ['alcohol', 'blood_thinners', 'aspirin']:  # Common interaction drugs
                    common_interactions.append(f"{drug1} with {other_drug}: {interaction}")
        
        if normalized_drug2 in COMMON_DRUG_INFO:
            for other_drug, interaction in COMMON_DRUG_INFO[normalized_drug2].get('interactions', {}).items():
                if other_drug in ['alcohol', 'blood_thinners', 'aspirin']:  # Common interaction drugs
                    common_interactions.append(f"{drug2} with {other_drug}: {interaction}")
        
        if common_interactions:
            return {
                'drug1': drug1,
                'drug2': drug2,
                'interaction': 'No direct interaction found between these drugs. However, here are some important interactions to be aware of:\n' + '\n'.join(common_interactions),
                'severity': 'moderate',
                'is_safe': True,
                'recommendation': 'Please consult your healthcare provider for personalized advice.'
            }
        
        return {
            'drug1': drug1,
            'drug2': drug2,
            'interaction': 'No specific interaction information available. Please consult your healthcare provider for guidance.',
            'severity': 'unknown',
            'is_safe': True,
            'recommendation': 'Always consult your healthcare provider before combining medications or consuming alcohol with medications.'
        }
    except Exception as e:
        logger.error(f"Error checking drug interaction between {drug1} and {drug2}: {str(e)}")
        return {
            'drug1': drug1,
            'drug2': drug2,
            'interaction': 'Unable to check drug interactions at this time. Please consult your healthcare provider.',
            'severity': 'unknown',
            'is_safe': True,
            'recommendation': 'Always consult your healthcare provider before combining medications or consuming alcohol with medications.'
        }

# Example usage
if __name__ == "__main__":
    # Single drug example
    print("--- Ibuprofen Info ---")
    ibuprofen_info = get_fda_data("ibuprofen")
    print(ibuprofen_info)
    
    # Interaction check example
    print("\n--- Ibuprofen + Acetaminophen Interaction ---")
    safe, result = check_drug_interaction(["ibuprofen", "acetaminophen"])
    print(f"Safe: {safe}")
    print(f"Result: {result}")
    
    # Critical interaction example
    print("\n--- Acetaminophen + Alcohol Interaction ---")
    safe, result = check_drug_interaction(["acetaminophen", "alcohol"])
    print(f"Safe: {safe}")
    print(f"Result: {result}")