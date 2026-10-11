from django.core.management.base import BaseCommand
from laboratory.models import LaboratoryTest


# ============================================================
# Laboratory Tests Seed Data
# 220+ Common Laboratory Tests
# ============================================================

TESTS = [

    # ========================================================
    # HEMATOLOGY
    # ========================================================

    ("CBC-WBC", "White Blood Cell Count", "عدد كريات الدم البيضاء",
     "Hematology", "WHOLE_BLOOD", "x10^3/uL", "4.0-11.0"),

    ("CBC-RBC", "Red Blood Cell Count", "عدد كريات الدم الحمراء",
     "Hematology", "WHOLE_BLOOD", "x10^6/uL", "Male: 4.5-5.9 | Female: 4.0-5.2"),

    ("CBC-HGB", "Hemoglobin", "الهيموغلوبين",
     "Hematology", "WHOLE_BLOOD", "g/dL", "Male: 13.5-17.5 | Female: 12.0-16.0"),

    ("CBC-HCT", "Hematocrit", "الهيماتوكريت",
     "Hematology", "WHOLE_BLOOD", "%", "Male: 41-53 | Female: 36-46"),

    ("CBC-MCV", "Mean Corpuscular Volume", "متوسط حجم الكرية",
     "Hematology", "WHOLE_BLOOD", "fL", "80-100"),

    ("CBC-MCH", "Mean Corpuscular Hemoglobin", "متوسط هيموغلوبين الكرية",
     "Hematology", "WHOLE_BLOOD", "pg", "27-33"),

    ("CBC-MCHC", "Mean Corpuscular Hemoglobin Concentration", "تركيز هيموغلوبين الكرية",
     "Hematology", "WHOLE_BLOOD", "g/dL", "32-36"),

    ("CBC-RDW", "Red Cell Distribution Width", "توزيع حجم كريات الدم الحمراء",
     "Hematology", "WHOLE_BLOOD", "%", "11.5-14.5"),

    ("CBC-PLT", "Platelet Count", "عدد الصفائح الدموية",
     "Hematology", "WHOLE_BLOOD", "x10^3/uL", "150-450"),

    ("CBC-MPV", "Mean Platelet Volume", "متوسط حجم الصفائح",
     "Hematology", "WHOLE_BLOOD", "fL", "7.5-11.5"),

    ("CBC-NEU", "Neutrophils", "العدلات",
     "Hematology", "WHOLE_BLOOD", "%", "40-75"),

    ("CBC-LYM", "Lymphocytes", "الخلايا اللمفاوية",
     "Hematology", "WHOLE_BLOOD", "%", "20-45"),

    ("CBC-MONO", "Monocytes", "الخلايا الوحيدة",
     "Hematology", "WHOLE_BLOOD", "%", "2-10"),

    ("CBC-EOS", "Eosinophils", "الخلايا الحمضية",
     "Hematology", "WHOLE_BLOOD", "%", "1-6"),

    ("CBC-BASO", "Basophils", "الخلايا القاعدية",
     "Hematology", "WHOLE_BLOOD", "%", "0-2"),

    ("CBC-ANC", "Absolute Neutrophil Count", "العدد المطلق للعدلات",
     "Hematology", "WHOLE_BLOOD", "x10^3/uL", "1.5-7.5"),

    ("CBC-ALC", "Absolute Lymphocyte Count", "العدد المطلق للخلايا اللمفاوية",
     "Hematology", "WHOLE_BLOOD", "x10^3/uL", "1.0-4.0"),

    ("CBC-ABC", "Absolute Basophil Count", "العدد المطلق للخلايا القاعدية",
     "Hematology", "WHOLE_BLOOD", "x10^3/uL", "0.0-0.2"),

    ("CBC-AEC", "Absolute Eosinophil Count", "العدد المطلق للخلايا الحمضية",
     "Hematology", "WHOLE_BLOOD", "x10^3/uL", "0.0-0.5"),

    ("RETIC", "Reticulocyte Count", "عدد الخلايا الشبكية",
     "Hematology", "WHOLE_BLOOD", "%", "0.5-2.5"),

    ("ESR", "Erythrocyte Sedimentation Rate", "سرعة ترسيب كريات الدم الحمراء",
     "Hematology", "WHOLE_BLOOD", "mm/hr", "Male: 0-15 | Female: 0-20"),

    ("BLOOD-FILM", "Peripheral Blood Film", "لطاخة الدم المحيطية",
     "Hematology", "WHOLE_BLOOD", "", "Normal morphology"),

    ("SICKLE", "Sickle Cell Screen", "فحص الخلايا المنجلية",
     "Hematology", "WHOLE_BLOOD", "", "Negative"),

    ("G6PD", "Glucose-6-Phosphate Dehydrogenase", "إنزيم G6PD",
     "Hematology", "WHOLE_BLOOD", "U/g Hb", "5.5-8.8"),

    ("FERRITIN", "Ferritin", "الفيريتين",
     "Hematology", "SERUM", "ng/mL", "Male: 30-400 | Female: 15-150"),

    ("IRON", "Serum Iron", "حديد الدم",
     "Hematology", "SERUM", "ug/dL", "Male: 65-175 | Female: 50-170"),

    ("TIBC", "Total Iron Binding Capacity", "السعة الكلية لارتباط الحديد",
     "Hematology", "SERUM", "ug/dL", "250-450"),

    ("TRANSFERRIN", "Transferrin", "الترانسفيرين",
     "Hematology", "SERUM", "mg/dL", "200-360"),

    ("RETIC-ABS", "Absolute Reticulocyte Count", "العدد المطلق للخلايا الشبكية",
     "Hematology", "WHOLE_BLOOD", "x10^9/L", "25-100"),

    # ========================================================
    # COAGULATION
    # ========================================================

    ("PT", "Prothrombin Time", "زمن البروثرومبين",
     "Coagulation", "PLASMA", "sec", "11-14"),

    ("INR", "International Normalized Ratio", "النسبة المعيارية الدولية",
     "Coagulation", "PLASMA", "ratio", "0.8-1.2"),

    ("APTT", "Activated Partial Thromboplastin Time", "زمن الثرومبوبلاستين الجزئي المنشط",
     "Coagulation", "PLASMA", "sec", "25-35"),

    ("FIBRINOGEN", "Fibrinogen", "الفيبرينوجين",
     "Coagulation", "PLASMA", "mg/dL", "200-400"),

    ("D-DIMER", "D-Dimer", "دي دايمر",
     "Coagulation", "PLASMA", "mg/L FEU", "<0.50"),

    ("TT", "Thrombin Time", "زمن الثرومبين",
     "Coagulation", "PLASMA", "sec", "14-21"),

    ("ATIII", "Antithrombin III", "مضاد الثرومبين الثالث",
     "Coagulation", "PLASMA", "%", "80-120"),

    ("PROTEIN-C", "Protein C Activity", "نشاط البروتين C",
     "Coagulation", "PLASMA", "%", "70-140"),

    ("PROTEIN-S", "Protein S Activity", "نشاط البروتين S",
     "Coagulation", "PLASMA", "%", "60-140"),

    # ========================================================
    # BIOCHEMISTRY
    # ========================================================

    ("GLUCOSE", "Glucose", "الجلوكوز",
     "Biochemistry", "SERUM", "mg/dL", "Fasting: 70-99"),

    ("GLUCOSE-R", "Random Glucose", "سكر الدم العشوائي",
     "Biochemistry", "SERUM", "mg/dL", "70-140"),

    ("GLUCOSE-PP", "Postprandial Glucose", "سكر الدم بعد الأكل",
     "Biochemistry", "SERUM", "mg/dL", "<140"),

    ("UREA", "Blood Urea", "اليوريا",
     "Renal Function", "SERUM", "mg/dL", "15-45"),

    ("BUN", "Blood Urea Nitrogen", "نيتروجين اليوريا في الدم",
     "Renal Function", "SERUM", "mg/dL", "7-20"),

    ("CREAT", "Creatinine", "الكرياتينين",
     "Renal Function", "SERUM", "mg/dL", "Male: 0.7-1.3 | Female: 0.6-1.1"),

    ("URIC", "Uric Acid", "حمض اليوريك",
     "Renal Function", "SERUM", "mg/dL", "Male: 3.4-7.0 | Female: 2.4-6.0"),

    ("eGFR", "Estimated Glomerular Filtration Rate", "معدل الترشيح الكبيبي المقدر",
     "Renal Function", "SERUM", "mL/min/1.73m2", ">60"),

    ("NA", "Sodium", "الصوديوم",
     "Electrolytes", "SERUM", "mmol/L", "135-145"),

    ("K", "Potassium", "البوتاسيوم",
     "Electrolytes", "SERUM", "mmol/L", "3.5-5.1"),

    ("CL", "Chloride", "الكلوريد",
     "Electrolytes", "SERUM", "mmol/L", "98-107"),

    ("HCO3", "Bicarbonate", "البيكربونات",
     "Electrolytes", "SERUM", "mmol/L", "22-29"),

    ("CA", "Calcium", "الكالسيوم",
     "Electrolytes", "SERUM", "mg/dL", "8.5-10.5"),

    ("ION-CA", "Ionized Calcium", "الكالسيوم المتأين",
     "Electrolytes", "SERUM", "mmol/L", "1.12-1.32"),

    ("MG", "Magnesium", "المغنيسيوم",
     "Electrolytes", "SERUM", "mg/dL", "1.7-2.2"),

    ("PHOS", "Phosphorus", "الفوسفور",
     "Electrolytes", "SERUM", "mg/dL", "2.5-4.5"),

    ("OSM", "Serum Osmolality", "أسمولالية المصل",
     "Electrolytes", "SERUM", "mOsm/kg", "275-295"),

    # ========================================================
    # LIVER FUNCTION
    # ========================================================

    ("ALT", "Alanine Aminotransferase", "إنزيم ALT",
     "Liver Function", "SERUM", "U/L", "Male: 7-56 | Female: 7-45"),

    ("AST", "Aspartate Aminotransferase", "إنزيم AST",
     "Liver Function", "SERUM", "U/L", "Male: 10-40 | Female: 9-32"),

    ("ALP", "Alkaline Phosphatase", "الفوسفاتاز القلوي",
     "Liver Function", "SERUM", "U/L", "44-147"),

    ("GGT", "Gamma Glutamyl Transferase", "جاما جلوتاميل ترانسفيراز",
     "Liver Function", "SERUM", "U/L", "Male: 8-61 | Female: 5-36"),

    ("TBIL", "Total Bilirubin", "البيليروبين الكلي",
     "Liver Function", "SERUM", "mg/dL", "0.2-1.2"),

    ("DBIL", "Direct Bilirubin", "البيليروبين المباشر",
     "Liver Function", "SERUM", "mg/dL", "0.0-0.3"),

    ("IBIL", "Indirect Bilirubin", "البيليروبين غير المباشر",
     "Liver Function", "SERUM", "mg/dL", "0.2-0.9"),

    ("TP", "Total Protein", "البروتين الكلي",
     "Liver Function", "SERUM", "g/dL", "6.0-8.3"),

    ("ALB", "Albumin", "الألبومين",
     "Liver Function", "SERUM", "g/dL", "3.5-5.0"),

    ("GLOB", "Globulin", "الجلوبيولين",
     "Liver Function", "SERUM", "g/dL", "2.0-3.5"),

    ("A-G", "Albumin Globulin Ratio", "نسبة الألبومين إلى الجلوبيولين",
     "Liver Function", "SERUM", "ratio", "1.0-2.5"),

    ("LDH", "Lactate Dehydrogenase", "إنزيم LDH",
     "Liver Function", "SERUM", "U/L", "140-280"),

    ("CHOLIN", "Cholinesterase", "كولين إستيراز",
     "Liver Function", "SERUM", "U/L", "Male: 4620-11500 | Female: 3930-10800"),

    # ========================================================
    # LIPID PROFILE
    # ========================================================

    ("CHOL", "Total Cholesterol", "الكوليسترول الكلي",
     "Lipid Profile", "SERUM", "mg/dL", "<200"),

    ("TG", "Triglycerides", "الدهون الثلاثية",
     "Lipid Profile", "SERUM", "mg/dL", "<150"),

    ("HDL", "HDL Cholesterol", "الكوليسترول الجيد HDL",
     "Lipid Profile", "SERUM", "mg/dL", ">40"),

    ("LDL", "LDL Cholesterol", "الكوليسترول الضار LDL",
     "Lipid Profile", "SERUM", "mg/dL", "<100"),

    ("VLDL", "VLDL Cholesterol", "كوليسترول VLDL",
     "Lipid Profile", "SERUM", "mg/dL", "5-40"),

    ("NON-HDL", "Non-HDL Cholesterol", "الكوليسترول غير HDL",
     "Lipid Profile", "SERUM", "mg/dL", "<130"),

    ("TC-HDL", "Total Cholesterol / HDL Ratio", "نسبة الكوليسترول الكلي إلى HDL",
     "Lipid Profile", "SERUM", "ratio", "<5.0"),

    ("LDL-HDL", "LDL / HDL Ratio", "نسبة LDL إلى HDL",
     "Lipid Profile", "SERUM", "ratio", "<3.5"),

    # ========================================================
    # DIABETES
    # ========================================================

    ("HBA1C", "Hemoglobin A1c", "الهيموغلوبين السكري HbA1c",
     "Diabetes", "WHOLE_BLOOD", "%", "<5.7"),

    ("INSULIN", "Insulin", "الإنسولين",
     "Diabetes", "SERUM", "uIU/mL", "2.6-24.9"),

    ("C-PEPTIDE", "C-Peptide", "سي بيبتيد",
     "Diabetes", "SERUM", "ng/mL", "1.1-4.4"),

    ("FRUCTOSAMINE", "Fructosamine", "الفركتوزامين",
     "Diabetes", "SERUM", "umol/L", "200-285"),

    ("MICROALB", "Urine Microalbumin", "الزلال الدقيق في البول",
     "Diabetes", "URINE", "mg/L", "<30"),

    ("ACR", "Albumin Creatinine Ratio", "نسبة الألبومين إلى الكرياتينين",
     "Diabetes", "URINE", "mg/g", "<30"),

    # ========================================================
    # THYROID
    # ========================================================

    ("TSH", "Thyroid Stimulating Hormone", "الهرمون المحفز للغدة الدرقية",
     "Thyroid", "SERUM", "uIU/mL", "0.4-4.0"),

    ("FT4", "Free Thyroxine", "الثيروكسين الحر FT4",
     "Thyroid", "SERUM", "ng/dL", "0.8-1.8"),

    ("FT3", "Free Triiodothyronine", "ثلاثي يودوثيرونين الحر FT3",
     "Thyroid", "SERUM", "pg/mL", "2.3-4.2"),

    ("T4", "Total Thyroxine", "الثيروكسين الكلي T4",
     "Thyroid", "SERUM", "ug/dL", "5.0-12.0"),

    ("T3", "Total Triiodothyronine", "ثلاثي يودوثيرونين الكلي T3",
     "Thyroid", "SERUM", "ng/dL", "80-200"),

    ("ANTI-TPO", "Anti-Thyroid Peroxidase Antibody", "الأجسام المضادة لإنزيم بيروكسيداز الغدة الدرقية",
     "Thyroid", "SERUM", "IU/mL", "<35"),

    ("ANTI-TG", "Anti-Thyroglobulin Antibody", "الأجسام المضادة للثيروغلوبولين",
     "Thyroid", "SERUM", "IU/mL", "<40"),

    ("TG", "Thyroglobulin", "الثيروغلوبولين",
     "Thyroid", "SERUM", "ng/mL", "3-40"),

    # ========================================================
    # CARDIAC
    # ========================================================

    ("TROP-I", "Troponin I", "تروبونين I",
     "Cardiac", "SERUM", "ng/mL", "<0.04"),

    ("TROP-T", "Troponin T", "تروبونين T",
     "Cardiac", "SERUM", "ng/mL", "<0.014"),

    ("CK", "Creatine Kinase", "كرياتين كيناز",
     "Cardiac", "SERUM", "U/L", "Male: 39-308 | Female: 26-192"),

    ("CK-MB", "Creatine Kinase MB", "إنزيم CK-MB",
     "Cardiac", "SERUM", "ng/mL", "<5"),

    ("MYOGLOBIN", "Myoglobin", "الميوغلوبين",
     "Cardiac", "SERUM", "ng/mL", "Male: 28-72 | Female: 25-58"),

    ("BNP", "B-Type Natriuretic Peptide", "الببتيد المدر للصوديوم من النوع B",
     "Cardiac", "SERUM", "pg/mL", "<100"),

    ("NT-PROBNP", "NT-proBNP", "NT-proBNP",
     "Cardiac", "SERUM", "pg/mL", "<125"),

    # ========================================================
    # INFLAMMATION
    # ========================================================

    ("CRP", "C-Reactive Protein", "البروتين المتفاعل C",
     "Inflammation", "SERUM", "mg/L", "<5"),

    ("HSCRP", "High Sensitivity CRP", "البروتين المتفاعل عالي الحساسية",
     "Inflammation", "SERUM", "mg/L", "<3"),

    ("PCT", "Procalcitonin", "البروكالسيتونين",
     "Inflammation", "SERUM", "ng/mL", "<0.05"),

    ("FERRITIN-INF", "Ferritin - Inflammatory Marker", "الفيريتين",
     "Inflammation", "SERUM", "ng/mL", "See laboratory reference"),

    ("IL6", "Interleukin-6", "إنترلوكين 6",
     "Inflammation", "SERUM", "pg/mL", "<7"),

    # ========================================================
    # HORMONES
    # ========================================================

    ("FSH", "Follicle Stimulating Hormone", "الهرمون المنشط للحويصلة",
     "Hormones", "SERUM", "mIU/mL", "Adult: Lab-specific"),

    ("LH", "Luteinizing Hormone", "الهرمون اللوتيني",
     "Hormones", "SERUM", "mIU/mL", "Adult: Lab-specific"),

    ("PROLACTIN", "Prolactin", "البرولاكتين",
     "Hormones", "SERUM", "ng/mL", "Male: 4-15 | Female: 4-23"),

    ("ESTRADIOL", "Estradiol", "الإستراديول",
     "Hormones", "SERUM", "pg/mL", "Cycle-dependent"),

    ("PROGESTERONE", "Progesterone", "البروجسترون",
     "Hormones", "SERUM", "ng/mL", "Cycle-dependent"),

    ("TESTOSTERONE", "Total Testosterone", "التستوستيرون الكلي",
     "Hormones", "SERUM", "ng/dL", "Male: 300-1000 | Female: 15-70"),

    ("FREE-TEST", "Free Testosterone", "التستوستيرون الحر",
     "Hormones", "SERUM", "pg/mL", "Lab-specific"),

    ("CORTISOL-AM", "Morning Cortisol", "الكورتيزول الصباحي",
     "Hormones", "SERUM", "ug/dL", "5-25"),

    ("CORTISOL-PM", "Evening Cortisol", "الكورتيزول المسائي",
     "Hormones", "SERUM", "ug/dL", "2.5-12.5"),

    ("DHEA-S", "DHEA-Sulfate", "DHEA-S",
     "Hormones", "SERUM", "ug/dL", "Age and sex dependent"),

    ("ACTH", "Adrenocorticotropic Hormone", "الهرمون الموجه لقشر الكظر",
     "Hormones", "EDTA_PLASMA", "pg/mL", "10-60"),

    ("PTH", "Parathyroid Hormone", "هرمون الغدة جار الدرقية",
     "Hormones", "SERUM", "pg/mL", "15-65"),

    ("IGF1", "Insulin-like Growth Factor 1", "عامل النمو الشبيه بالإنسولين 1",
     "Hormones", "SERUM", "ng/mL", "Age dependent"),

    ("GH", "Growth Hormone", "هرمون النمو",
     "Hormones", "SERUM", "ng/mL", "Lab-specific"),

    # ========================================================
    # VITAMINS
    # ========================================================

    ("VIT-D", "25-Hydroxy Vitamin D", "فيتامين D",
     "Vitamins", "SERUM", "ng/mL", "30-100"),

    ("VIT-B12", "Vitamin B12", "فيتامين B12",
     "Vitamins", "SERUM", "pg/mL", "200-900"),

    ("FOLATE", "Folate", "حمض الفوليك",
     "Vitamins", "SERUM", "ng/mL", "4-20"),

    ("VIT-A", "Vitamin A", "فيتامين A",
     "Vitamins", "SERUM", "ug/dL", "20-60"),

    ("VIT-E", "Vitamin E", "فيتامين E",
     "Vitamins", "SERUM", "mg/L", "5.5-17"),

    ("VIT-B1", "Vitamin B1", "فيتامين B1",
     "Vitamins", "WHOLE_BLOOD", "nmol/L", "70-180"),

    ("VIT-B6", "Vitamin B6", "فيتامين B6",
     "Vitamins", "SERUM", "ug/L", "5-50"),

    # ========================================================
    # IRON / ANEMIA
    # ========================================================

    ("UIBC", "Unsaturated Iron Binding Capacity", "السعة غير المشبعة لارتباط الحديد",
     "Anemia", "SERUM", "ug/dL", "150-375"),

    ("TSAT", "Transferrin Saturation", "تشبع الترانسفيرين",
     "Anemia", "SERUM", "%", "20-50"),

    ("SOL-TRANS", "Soluble Transferrin Receptor", "مستقبل الترانسفيرين الذائب",
     "Anemia", "SERUM", "mg/L", "1.8-4.6"),

    # ========================================================
    # IMMUNOLOGY / AUTOIMMUNE
    # ========================================================

    ("ANA", "Antinuclear Antibody", "الأجسام المضادة للنواة ANA",
     "Immunology", "SERUM", "", "Negative"),

    ("ANA-TITER", "ANA Titer", "عيار ANA",
     "Immunology", "SERUM", "titer", "<1:80"),

    ("RF", "Rheumatoid Factor", "عامل الروماتويد",
     "Immunology", "SERUM", "IU/mL", "<14"),

    ("ANTI-CCP", "Anti-CCP Antibody", "الأجسام المضادة Anti-CCP",
     "Immunology", "SERUM", "U/mL", "<20"),

    ("C3", "Complement C3", "المتممة C3",
     "Immunology", "SERUM", "mg/dL", "90-180"),

    ("C4", "Complement C4", "المتممة C4",
     "Immunology", "SERUM", "mg/dL", "10-40"),

    ("IGE", "Total Immunoglobulin E", "الغلوبولين المناعي E الكلي",
     "Immunology", "SERUM", "IU/mL", "<100"),

    ("IGA", "Immunoglobulin A", "الغلوبولين المناعي A",
     "Immunology", "SERUM", "mg/dL", "70-400"),

    ("IGG", "Immunoglobulin G", "الغلوبولين المناعي G",
     "Immunology", "SERUM", "mg/dL", "700-1600"),

    ("IGM", "Immunoglobulin M", "الغلوبولين المناعي M",
     "Immunology", "SERUM", "mg/dL", "40-230"),

    ("ANTI-DSDNA", "Anti-dsDNA Antibody", "الأجسام المضادة للـDNA مزدوج السلسلة",
     "Immunology", "SERUM", "IU/mL", "<10"),

    ("ENA", "Extractable Nuclear Antigen Panel", "فحص ENA",
     "Immunology", "SERUM", "", "Negative"),

    ("SSA", "Anti-Ro/SSA", "الأجسام المضادة SSA",
     "Immunology", "SERUM", "", "Negative"),

    ("SSB", "Anti-La/SSB", "الأجسام المضادة SSB",
     "Immunology", "SERUM", "", "Negative"),

    # ========================================================
    # INFECTIOUS DISEASES - VIRAL
    # ========================================================

    ("HBsAg", "Hepatitis B Surface Antigen", "مستضد سطح التهاب الكبد B",
     "Infectious Diseases", "SERUM", "", "Non-Reactive"),

    ("Anti-HBs", "Hepatitis B Surface Antibody", "الأجسام المضادة لالتهاب الكبد B",
     "Infectious Diseases", "SERUM", "mIU/mL", ">=10 protective"),

    ("Anti-HBc", "Hepatitis B Core Antibody", "الأجسام المضادة لنواة التهاب الكبد B",
     "Infectious Diseases", "SERUM", "", "Non-Reactive"),

    ("HBeAg", "Hepatitis B e Antigen", "مستضد e لالتهاب الكبد B",
     "Infectious Diseases", "SERUM", "", "Non-Reactive"),

    ("Anti-HBe", "Hepatitis B e Antibody", "الأجسام المضادة لـ HBe",
     "Infectious Diseases", "SERUM", "", "Non-Reactive"),

    ("Anti-HCV", "Hepatitis C Antibody", "الأجسام المضادة لالتهاب الكبد C",
     "Infectious Diseases", "SERUM", "", "Non-Reactive"),

    ("HCV-RNA", "Hepatitis C RNA", "RNA لفيروس التهاب الكبد C",
     "Infectious Diseases", "SERUM", "IU/mL", "Not Detected"),

    ("HIV-AgAb", "HIV 1/2 Antigen/Antibody", "فحص HIV 1/2 المستضد والأجسام المضادة",
     "Infectious Diseases", "SERUM", "", "Non-Reactive"),

    ("HAV-IGM", "Hepatitis A IgM", "التهاب الكبد A IgM",
     "Infectious Diseases", "SERUM", "", "Non-Reactive"),

    ("HAV-IGG", "Hepatitis A IgG", "التهاب الكبد A IgG",
     "Infectious Diseases", "SERUM", "", "Negative"),

    ("HEV-IGM", "Hepatitis E IgM", "التهاب الكبد E IgM",
     "Infectious Diseases", "SERUM", "", "Non-Reactive"),

    ("CMV-IGM", "CMV IgM", "CMV IgM",
     "Infectious Diseases", "SERUM", "", "Negative"),

    ("CMV-IGG", "CMV IgG", "CMV IgG",
     "Infectious Diseases", "SERUM", "", "Negative"),

    ("EBV-VCA-IGM", "EBV VCA IgM", "EBV VCA IgM",
     "Infectious Diseases", "SERUM", "", "Negative"),

    ("EBV-VCA-IGG", "EBV VCA IgG", "EBV VCA IgG",
     "Infectious Diseases", "SERUM", "", "Negative"),

    ("EBV-EBNA", "EBV EBNA IgG", "EBV EBNA IgG",
     "Infectious Diseases", "SERUM", "", "Negative"),

    ("HSV1-IGM", "HSV-1 IgM", "HSV-1 IgM",
     "Infectious Diseases", "SERUM", "", "Negative"),

    ("HSV1-IGG", "HSV-1 IgG", "HSV-1 IgG",
     "Infectious Diseases", "SERUM", "", "Negative"),

    ("HSV2-IGM", "HSV-2 IgM", "HSV-2 IgM",
     "Infectious Diseases", "SERUM", "", "Negative"),

    ("HSV2-IGG", "HSV-2 IgG", "HSV-2 IgG",
     "Infectious Diseases", "SERUM", "", "Negative"),

    # ========================================================
    # TORCH / PREGNANCY
    # ========================================================

    ("TOXO-IGM", "Toxoplasma IgM", "داء المقوسات IgM",
     "TORCH", "SERUM", "", "Negative"),

    ("TOXO-IGG", "Toxoplasma IgG", "داء المقوسات IgG",
     "TORCH", "SERUM", "IU/mL", "<8"),

    ("RUBELLA-IGM", "Rubella IgM", "الحصبة الألمانية IgM",
     "TORCH", "SERUM", "", "Negative"),

    ("RUBELLA-IGG", "Rubella IgG", "الحصبة الألمانية IgG",
     "TORCH", "SERUM", "IU/mL", ">=10 Immune"),

    ("CMV-TORCH-IGM", "CMV IgM - TORCH", "CMV IgM",
     "TORCH", "SERUM", "", "Negative"),

    ("CMV-TORCH-IGG", "CMV IgG - TORCH", "CMV IgG",
     "TORCH", "SERUM", "", "Negative"),

    # ========================================================
    # BACTERIAL SEROLOGY
    # ========================================================

    ("ASO", "Anti-Streptolysin O", "مضاد الستربتوليزين O",
     "Serology", "SERUM", "IU/mL", "<200"),

    ("WIDAL-O", "Widal O Antigen", "اختبار فيدال O",
     "Serology", "SERUM", "titer", "<1:80"),

    ("WIDAL-H", "Widal H Antigen", "اختبار فيدال H",
     "Serology", "SERUM", "titer", "<1:80"),

    ("WIDAL-AH", "Widal AH Antigen", "اختبار فيدال AH",
     "Serology", "SERUM", "titer", "<1:80"),

    ("WIDAL-BH", "Widal BH Antigen", "اختبار فيدال BH",
     "Serology", "SERUM", "titer", "<1:80"),

    ("BRUCELLA-IgG", "Brucella IgG", "البروسيلا IgG",
     "Serology", "SERUM", "", "Negative"),

    ("BRUCELLA-IgM", "Brucella IgM", "البروسيلا IgM",
     "Serology", "SERUM", "", "Negative"),

    # ========================================================
    # MALARIA / PARASITOLOGY
    # ========================================================

    ("MALARIA-PF", "Malaria Plasmodium falciparum", "ملاريا المتصورة المنجلية",
     "Parasitology", "WHOLE_BLOOD", "", "Negative"),

    ("MALARIA-PAN", "Malaria Pan Antigen", "مستضد الملاريا العام",
     "Parasitology", "WHOLE_BLOOD", "", "Negative"),

    ("MALARIA-FILM", "Malaria Blood Film", "فيلم دم للملاريا",
     "Parasitology", "WHOLE_BLOOD", "", "No parasites seen"),

    ("MALARIA-RDT", "Malaria Rapid Diagnostic Test", "فحص الملاريا السريع",
     "Parasitology", "WHOLE_BLOOD", "", "Negative"),

    ("MICROF", "Microfilaria", "الميكروفيلاريا",
     "Parasitology", "WHOLE_BLOOD", "", "Not detected"),

    # ========================================================
    # URINALYSIS
    # ========================================================

    ("UR-COLOR", "Urine Color", "لون البول",
     "Urinalysis", "URINE", "", "Pale yellow"),

    ("UR-APPEAR", "Urine Appearance", "مظهر البول",
     "Urinalysis", "URINE", "", "Clear"),

    ("UR-PH", "Urine pH", "درجة حموضة البول",
     "Urinalysis", "URINE", "", "4.5-8.0"),

    ("UR-SG", "Urine Specific Gravity", "الكثافة النوعية للبول",
     "Urinalysis", "URINE", "", "1.005-1.030"),

    ("UR-PRO", "Urine Protein", "بروتين البول",
     "Urinalysis", "URINE", "mg/dL", "Negative"),

    ("UR-GLU", "Urine Glucose", "جلوكوز البول",
     "Urinalysis", "URINE", "mg/dL", "Negative"),

    ("UR-KET", "Urine Ketones", "كيتونات البول",
     "Urinalysis", "URINE", "", "Negative"),

    ("UR-BLD", "Urine Blood", "دم في البول",
     "Urinalysis", "URINE", "", "Negative"),

    ("UR-BIL", "Urine Bilirubin", "بيليروبين البول",
     "Urinalysis", "URINE", "", "Negative"),

    ("UR-URO", "Urobilinogen", "يوروبيلينوجين البول",
     "Urinalysis", "URINE", "mg/dL", "0.2-1.0"),

    ("UR-NIT", "Urine Nitrite", "نيتريت البول",
     "Urinalysis", "URINE", "", "Negative"),

    ("UR-LEU", "Urine Leukocyte Esterase", "إنزيم كريات الدم البيضاء في البول",
     "Urinalysis", "URINE", "", "Negative"),

    ("UR-WBC", "Urine White Blood Cells", "كريات الدم البيضاء في البول",
     "Urinalysis", "URINE", "/HPF", "0-5"),

    ("UR-RBC", "Urine Red Blood Cells", "كريات الدم الحمراء في البول",
     "Urinalysis", "URINE", "/HPF", "0-2"),

    ("UR-EP", "Urine Epithelial Cells", "الخلايا الطلائية في البول",
     "Urinalysis", "URINE", "/HPF", "Few"),

    ("UR-CAST", "Urine Casts", "أسطوانات البول",
     "Urinalysis", "URINE", "/LPF", "None/Few Hyaline"),

    ("UR-CRYSTAL", "Urine Crystals", "بلورات البول",
     "Urinalysis", "URINE", "", "None"),

    ("UR-YEAST", "Urine Yeast", "خمائر البول",
     "Urinalysis", "URINE", "", "None"),

    ("UR-BACT", "Urine Bacteria", "بكتيريا البول",
     "Urinalysis", "URINE", "", "None"),

    # ========================================================
    # STOOL
    # ========================================================

    ("STOOL-COLOR", "Stool Color", "لون البراز",
     "Stool Analysis", "STOOL", "", "Brown"),

    ("STOOL-CONS", "Stool Consistency", "قوام البراز",
     "Stool Analysis", "STOOL", "", "Formed"),

    ("STOOL-OVA", "Stool Ova", "بيض الطفيليات في البراز",
     "Parasitology", "STOOL", "", "Not seen"),

    ("STOOL-PARA", "Stool Parasites", "طفيليات البراز",
     "Parasitology", "STOOL", "", "Not seen"),

    ("STOOL-ENTAMOEBA", "Entamoeba histolytica", "الأميبا Entamoeba histolytica",
     "Parasitology", "STOOL", "", "Not seen"),

    ("STOOL-GIARDIA", "Giardia lamblia", "الجيارديا",
     "Parasitology", "STOOL", "", "Not seen"),

    ("STOOL-ASCARIS", "Ascaris lumbricoides", "الإسكارس",
     "Parasitology", "STOOL", "", "Not seen"),

    ("STOOL-HOOK", "Hookworm", "الدودة الخطافية",
     "Parasitology", "STOOL", "", "Not seen"),

    ("STOOL-STRONG", "Strongyloides stercoralis", "Strongyloides stercoralis",
     "Parasitology", "STOOL", "", "Not seen"),

    ("STOOL-TRICHO", "Trichuris trichiura", "Trichuris trichiura",
     "Parasitology", "STOOL", "", "Not seen"),

    ("STOOL-OCCULT", "Fecal Occult Blood", "الدم الخفي في البراز",
     "Stool Analysis", "STOOL", "", "Negative"),

    ("STOOL-WBC", "Stool White Blood Cells", "كريات الدم البيضاء في البراز",
     "Stool Analysis", "STOOL", "/HPF", "None"),

    ("STOOL-RBC", "Stool Red Blood Cells", "كريات الدم الحمراء في البراز",
     "Stool Analysis", "STOOL", "/HPF", "None"),

    # ========================================================
    # MICROBIOLOGY
    # ========================================================

    ("URINE-CULT", "Urine Culture", "مزرعة البول",
     "Microbiology", "URINE", "", "No growth"),

    ("BLOOD-CULT", "Blood Culture", "مزرعة الدم",
     "Microbiology", "WHOLE_BLOOD", "", "No growth"),

    ("STOOL-CULT", "Stool Culture", "مزرعة البراز",
     "Microbiology", "STOOL", "", "No pathogenic growth"),

    ("WOUND-CULT", "Wound Culture", "مزرعة الجرح",
     "Microbiology", "SWAB", "", "No growth"),

    ("THROAT-CULT", "Throat Culture", "مزرعة الحلق",
     "Microbiology", "SWAB", "", "No pathogenic growth"),

    ("SPUTUM-CULT", "Sputum Culture", "مزرعة البلغم",
     "Microbiology", "OTHER", "", "No pathogenic growth"),

    ("VAGINAL-CULT", "Vaginal Culture", "مزرعة المهبل",
     "Microbiology", "SWAB", "", "No pathogenic growth"),

    ("SEMEN-CULT", "Semen Culture", "مزرعة السائل المنوي",
     "Microbiology", "OTHER", "", "No growth"),

    ("GRAM", "Gram Stain", "صبغة جرام",
     "Microbiology", "SWAB", "", "No organisms seen"),

    ("AFB-STAIN", "Acid Fast Bacilli Stain", "صبغة العصيات المقاومة للحمض",
     "Microbiology", "OTHER", "", "Negative"),

    ("KOH", "KOH Preparation", "فحص KOH للفطريات",
     "Microbiology", "SWAB", "", "No fungal elements"),

    ("CSF-CULT", "CSF Culture", "مزرعة السائل النخاعي",
     "Microbiology", "CSF", "", "No growth"),

    # ========================================================
    # SEMEN ANALYSIS
    # ========================================================

    ("SEM-VOL", "Semen Volume", "حجم السائل المنوي",
     "Semen Analysis", "OTHER", "mL", ">=1.4"),

    ("SEM-PH", "Semen pH", "درجة حموضة السائل المنوي",
     "Semen Analysis", "OTHER", "", ">=7.2"),

    ("SEM-CONC", "Sperm Concentration", "تركيز الحيوانات المنوية",
     "Semen Analysis", "OTHER", "million/mL", ">=16"),

    ("SEM-TOTAL", "Total Sperm Number", "العدد الكلي للحيوانات المنوية",
     "Semen Analysis", "OTHER", "million", ">=39"),

    ("SEM-MOT", "Sperm Motility", "حركة الحيوانات المنوية",
     "Semen Analysis", "OTHER", "%", "Progressive >=30"),

    ("SEM-MORPH", "Sperm Morphology", "شكل الحيوانات المنوية",
     "Semen Analysis", "OTHER", "%", "Normal forms >=4"),

    ("SEM-WBC", "Semen White Blood Cells", "كريات الدم البيضاء في السائل المنوي",
     "Semen Analysis", "OTHER", "million/mL", "<1"),

    ("SEM-VISC", "Semen Viscosity", "لزوجة السائل المنوي",
     "Semen Analysis", "OTHER", "", "Normal"),

    # ========================================================
    # BLOOD BANK
    # ========================================================

    ("ABO", "ABO Blood Group", "فصيلة الدم ABO",
     "Blood Bank", "WHOLE_BLOOD", "", "A/B/AB/O"),

    ("RH", "Rh(D) Blood Group", "عامل Rh",
     "Blood Bank", "WHOLE_BLOOD", "", "Positive/Negative"),

    ("CROSSMATCH", "Blood Crossmatch", "اختبار التوافق",
     "Blood Bank", "WHOLE_BLOOD", "", "Compatible"),

    ("DAT", "Direct Antiglobulin Test", "اختبار كومبس المباشر",
     "Blood Bank", "WHOLE_BLOOD", "", "Negative"),

    ("IAT", "Indirect Antiglobulin Test", "اختبار كومبس غير المباشر",
     "Blood Bank", "SERUM", "", "Negative"),

    ("ANTIBODY-SCREEN", "Red Cell Antibody Screen", "فحص الأجسام المضادة لخلايا الدم",
     "Blood Bank", "SERUM", "", "Negative"),

    # ========================================================
    # CSF
    # ========================================================

    ("CSF-APPEAR", "CSF Appearance", "مظهر السائل النخاعي",
     "CSF Analysis", "CSF", "", "Clear"),

    ("CSF-WBC", "CSF White Blood Cells", "كريات الدم البيضاء في السائل النخاعي",
     "CSF Analysis", "CSF", "cells/uL", "0-5"),

    ("CSF-RBC", "CSF Red Blood Cells", "كريات الدم الحمراء في السائل النخاعي",
     "CSF Analysis", "CSF", "cells/uL", "0"),

    ("CSF-PRO", "CSF Protein", "بروتين السائل النخاعي",
     "CSF Analysis", "CSF", "mg/dL", "15-45"),

    ("CSF-GLU", "CSF Glucose", "جلوكوز السائل النخاعي",
     "CSF Analysis", "CSF", "mg/dL", "40-70"),

    ("CSF-CHLORIDE", "CSF Chloride", "كلوريد السائل النخاعي",
     "CSF Analysis", "CSF", "mmol/L", "118-132"),

    # ========================================================
    # TUMOR MARKERS
    # ========================================================

    ("AFP", "Alpha Fetoprotein", "ألفا فيتو بروتين",
     "Tumor Markers", "SERUM", "ng/mL", "<10"),

    ("CEA", "Carcinoembryonic Antigen", "المستضد السرطاني الجنيني",
     "Tumor Markers", "SERUM", "ng/mL", "Non-smoker <3 | Smoker <5"),

    ("CA125", "Cancer Antigen 125", "المستضد السرطاني CA-125",
     "Tumor Markers", "SERUM", "U/mL", "<35"),

    ("CA153", "Cancer Antigen 15-3", "المستضد السرطاني CA 15-3",
     "Tumor Markers", "SERUM", "U/mL", "<30"),

    ("CA199", "Cancer Antigen 19-9", "المستضد السرطاني CA 19-9",
     "Tumor Markers", "SERUM", "U/mL", "<37"),

    ("PSA", "Prostate Specific Antigen", "المستضد النوعي للبروستاتا",
     "Tumor Markers", "SERUM", "ng/mL", "<4"),

    ("FREE-PSA", "Free PSA", "PSA الحر",
     "Tumor Markers", "SERUM", "ng/mL", "Lab-specific"),

    ("BETA-HCG", "Beta hCG", "بيتا hCG",
     "Pregnancy", "SERUM", "mIU/mL", "<5"),

    # ========================================================
    # PREGNANCY
    # ========================================================

    ("PREG-URINE", "Urine Pregnancy Test", "اختبار الحمل في البول",
     "Pregnancy", "URINE", "", "Negative"),

    ("PREG-SERUM", "Serum Pregnancy Test", "اختبار الحمل في الدم",
     "Pregnancy", "SERUM", "", "Negative"),

    ("BHCG-QUANT", "Quantitative Beta hCG", "بيتا hCG كمي",
     "Pregnancy", "SERUM", "mIU/mL", "<5"),

    # ========================================================
    # PANCREATIC
    # ========================================================

    ("AMYLASE", "Amylase", "الأميليز",
     "Pancreatic", "SERUM", "U/L", "30-110"),

    ("LIPASE", "Lipase", "الليباز",
     "Pancreatic", "SERUM", "U/L", "13-60"),

    ("TRYPSIN", "Trypsin", "التربسين",
     "Pancreatic", "SERUM", "ng/mL", "Lab-specific"),

    # ========================================================
    # MUSCLE / ENZYMES
    # ========================================================

    ("ALDOLASE", "Aldolase", "ألدولاز",
     "Muscle Enzymes", "SERUM", "U/L", "1.0-7.5"),

    ("CK-TOTAL", "Total Creatine Kinase", "كرياتين كيناز الكلي",
     "Muscle Enzymes", "SERUM", "U/L", "Male: 39-308 | Female: 26-192"),

    # ========================================================
    # TRACE ELEMENTS
    # ========================================================

    ("ZINC", "Zinc", "الزنك",
     "Trace Elements", "SERUM", "ug/dL", "60-120"),

    ("COPPER", "Copper", "النحاس",
     "Trace Elements", "SERUM", "ug/dL", "70-140"),

    ("SELENIUM", "Selenium", "السيلينيوم",
     "Trace Elements", "SERUM", "ug/L", "70-150"),

    # ========================================================
    # ELECTROLYTES / METABOLIC
    # ========================================================

    ("LACTATE", "Lactate", "اللاكتات",
     "Metabolic", "PLASMA", "mmol/L", "0.5-2.2"),

    ("AMMONIA", "Ammonia", "الأمونيا",
     "Metabolic", "PLASMA", "umol/L", "15-45"),

    ("BETA-HYDROXY", "Beta-Hydroxybutyrate", "بيتا هيدروكسي بيوتيرات",
     "Metabolic", "SERUM", "mmol/L", "<0.6"),

    # ========================================================
    # ABG
    # ========================================================

    ("ABG-PH", "Arterial Blood pH", "درجة حموضة الدم الشرياني",
     "Blood Gas", "WHOLE_BLOOD", "", "7.35-7.45"),

    ("ABG-PCO2", "Arterial pCO2", "الضغط الجزئي لثاني أكسيد الكربون",
     "Blood Gas", "WHOLE_BLOOD", "mmHg", "35-45"),

    ("ABG-PO2", "Arterial pO2", "الضغط الجزئي للأكسجين",
     "Blood Gas", "WHOLE_BLOOD", "mmHg", "80-100"),

    ("ABG-HCO3", "Arterial Bicarbonate", "البيكربونات الشريانية",
     "Blood Gas", "WHOLE_BLOOD", "mmol/L", "22-26"),

    ("ABG-BE", "Base Excess", "فائض القاعدة",
     "Blood Gas", "WHOLE_BLOOD", "mmol/L", "-2 to +2"),

    ("ABG-SO2", "Arterial Oxygen Saturation", "تشبع الأكسجين الشرياني",
     "Blood Gas", "WHOLE_BLOOD", "%", "95-100"),

    # ========================================================
    # ADDITIONAL CHEMISTRY
    # ========================================================

    ("BICARB", "Serum Bicarbonate", "بيكربونات المصل",
     "Biochemistry", "SERUM", "mmol/L", "22-29"),

    ("ANION-GAP", "Anion Gap", "الفجوة الأيونية",
     "Biochemistry", "SERUM", "mmol/L", "8-16"),

    ("CALC-OSM", "Calculated Osmolality", "الأسمولالية المحسوبة",
     "Biochemistry", "SERUM", "mOsm/kg", "275-295"),

    ("LIPASE-PAN", "Pancreatic Lipase", "ليباز البنكرياس",
     "Pancreatic", "SERUM", "U/L", "13-60"),

    # ========================================================
    # MORE SEROLOGY
    # ========================================================

    ("DENGUE-NS1", "Dengue NS1 Antigen", "مستضد حمى الضنك NS1",
     "Infectious Diseases", "SERUM", "", "Negative"),

    ("DENGUE-IGM", "Dengue IgM", "حمى الضنك IgM",
     "Infectious Diseases", "SERUM", "", "Negative"),

    ("DENGUE-IGG", "Dengue IgG", "حمى الضنك IgG",
     "Infectious Diseases", "SERUM", "", "Negative"),

    ("CHIK-IGM", "Chikungunya IgM", "شيكونغونيا IgM",
     "Infectious Diseases", "SERUM", "", "Negative"),

    ("CHIK-IGG", "Chikungunya IgG", "شيكونغونيا IgG",
     "Infectious Diseases", "SERUM", "", "Negative"),

    ("COVID-AG", "SARS-CoV-2 Antigen", "مستضد SARS-CoV-2",
     "Infectious Diseases", "SWAB", "", "Negative"),

    ("COVID-IGG", "SARS-CoV-2 IgG", "SARS-CoV-2 IgG",
     "Infectious Diseases", "SERUM", "", "Negative"),

    ("COVID-IGM", "SARS-CoV-2 IgM", "SARS-CoV-2 IgM",
     "Infectious Diseases", "SERUM", "", "Negative"),

    # ========================================================
    # MORE HORMONES
    # ========================================================

    ("SHBG", "Sex Hormone Binding Globulin", "الجلوبيولين الرابط للهرمونات الجنسية",
     "Hormones", "SERUM", "nmol/L", "Male: 10-57 | Female: 18-144"),

    ("AMH", "Anti-Mullerian Hormone", "الهرمون المضاد لمولر",
     "Hormones", "SERUM", "ng/mL", "Age dependent"),

    ("17-OHP", "17-Hydroxyprogesterone", "17 هيدروكسي بروجسترون",
     "Hormones", "SERUM", "ng/dL", "Lab-specific"),

    ("DHEA", "DHEA", "ديهيدرو إيبي أندروستيرون",
     "Hormones", "SERUM", "ug/dL", "Age dependent"),

    ("ALDOSTERONE", "Aldosterone", "الألدوستيرون",
     "Hormones", "SERUM", "ng/dL", "Position dependent"),

    ("RENIN", "Renin", "الرينين",
     "Hormones", "PLASMA", "ng/mL/hr", "Lab-specific"),

    # ========================================================
    # MORE VITAMINS / NUTRITION
    # ========================================================

    ("HOMOCYSTEINE", "Homocysteine", "الهوموسيستين",
     "Vitamins", "SERUM", "umol/L", "5-15"),

    ("MMA", "Methylmalonic Acid", "حمض ميثيل مالونيك",
     "Vitamins", "SERUM", "umol/L", "0.08-0.56"),

    # ========================================================
    # ADDITIONAL RENAL
    # ========================================================

    ("CYSTATIN-C", "Cystatin C", "سيستاتين C",
     "Renal Function", "SERUM", "mg/L", "0.62-1.11"),

    ("URINE-CREAT", "Urine Creatinine", "كرياتينين البول",
     "Renal Function", "URINE", "mg/dL", "Male: 20-320 | Female: 20-275"),

    ("URINE-UREA", "Urine Urea", "يوريا البول",
     "Renal Function", "URINE", "mg/dL", "Lab-specific"),

    # ========================================================
    # ADDITIONAL LIVER
    # ========================================================

    ("5NT", "5'-Nucleotidase", "5 نيوكليوتيداز",
     "Liver Function", "SERUM", "U/L", "2-17"),

    ("BILE-ACIDS", "Total Bile Acids", "الأحماض الصفراوية الكلية",
     "Liver Function", "SERUM", "umol/L", "0-10"),

    # ========================================================
    # FINAL GENERAL TESTS
    # ========================================================

    ("CALCIUM-CORR", "Corrected Calcium", "الكالسيوم المصحح",
     "Biochemistry", "SERUM", "mg/dL", "8.5-10.5"),

    ("PHOS-URINE", "Urine Phosphate", "فوسفات البول",
     "Renal Function", "URINE", "mg/dL", "Lab-specific"),

    ("SODIUM-URINE", "Urine Sodium", "صوديوم البول",
     "Renal Function", "URINE", "mmol/L", "Lab-specific"),

    ("POTASSIUM-URINE", "Urine Potassium", "بوتاسيوم البول",
     "Renal Function", "URINE", "mmol/L", "Lab-specific"),

    ("CHLORIDE-URINE", "Urine Chloride", "كلوريد البول",
     "Renal Function", "URINE", "mmol/L", "Lab-specific"),

]


class Command(BaseCommand):
    help = "Seed laboratory tests into the database"

    def handle(self, *args, **options):

        created_count = 0
        updated_count = 0

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "=============================================="
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "   LABORATORY TESTS SEEDING"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "=============================================="
            )
        )
        self.stdout.write("")

        for (
            code,
            name_en,
            name_ar,
            category,
            sample_type,
            unit,
            reference_range,
        ) in TESTS:

            obj, created = LaboratoryTest.objects.update_or_create(
                code=code,
                defaults={
                    "name_en": name_en,
                    "name_ar": name_ar,
                    "category": category,
                    "sample_type": sample_type,
                    "unit": unit,
                    "reference_range": reference_range,
                    "price": 0,
                    "is_active": True,
                },
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[ADDED] {code} - {name_en}"
                    )
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"[UPDATED] {code} - {name_en}"
                    )
                )

        total = LaboratoryTest.objects.count()

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "=============================================="
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Added:   {created_count}"
            )
        )

        self.stdout.write(
            self.style.WARNING(
                f"Updated: {updated_count}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Total laboratory tests in database: {total}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "=============================================="
            )
        )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Laboratory test seeding completed successfully."
            )
        )
