from django.core.management.base import BaseCommand
from laboratory.models import LaboratoryTest
from departments.models import Department


TESTS = [

# =========================================================
# HEMATOLOGY
# =========================================================
("HEM001","Complete Blood Count (CBC)","تعداد دم كامل","Hematology","WHOLE_BLOOD","", "Lab-dependent"),
("HEM002","Hemoglobin (Hb)","الهيموغلوبين","Hematology","WHOLE_BLOOD","g/dL","M: 13-17; F: 12-15"),
("HEM003","Hematocrit (HCT)","الهيماتوكريت","Hematology","WHOLE_BLOOD","%","M: 40-52; F: 36-48"),
("HEM004","RBC Count","عدد كريات الدم الحمراء","Hematology","WHOLE_BLOOD","10^6/µL","M: 4.5-5.9; F: 4.0-5.2"),
("HEM005","WBC Count","عدد كريات الدم البيضاء","Hematology","WHOLE_BLOOD","10^3/µL","4.0-11.0"),
("HEM006","Platelet Count","عدد الصفائح الدموية","Hematology","WHOLE_BLOOD","10^3/µL","150-450"),
("HEM007","MCV","متوسط حجم الكرية","Hematology","WHOLE_BLOOD","fL","80-100"),
("HEM008","MCH","متوسط هيموغلوبين الكرية","Hematology","WHOLE_BLOOD","pg","27-33"),
("HEM009","MCHC","متوسط تركيز هيموغلوبين الكرية","Hematology","WHOLE_BLOOD","g/dL","32-36"),
("HEM010","RDW","تفاوت حجم كريات الدم الحمراء","Hematology","WHOLE_BLOOD","%","11.5-14.5"),
("HEM011","Neutrophils","العدلات","Hematology","WHOLE_BLOOD","%","40-75"),
("HEM012","Lymphocytes","الخلايا اللمفاوية","Hematology","WHOLE_BLOOD","%","20-45"),
("HEM013","Monocytes","الخلايا الوحيدة","Hematology","WHOLE_BLOOD","%","2-10"),
("HEM014","Eosinophils","الخلايا الحمضية","Hematology","WHOLE_BLOOD","%","1-6"),
("HEM015","Basophils","الخلايا القاعدية","Hematology","WHOLE_BLOOD","%","0-2"),
("HEM016","ESR","سرعة ترسيب الدم","Hematology","WHOLE_BLOOD","mm/hr","Lab-dependent"),
("HEM017","Reticulocyte Count","عدد الخلايا الشبكية","Hematology","WHOLE_BLOOD","%","0.5-2.5"),
("HEM018","Peripheral Blood Smear","لطاخة الدم المحيطية","Hematology","WHOLE_BLOOD","","Report morphology"),

# =========================================================
# CLINICAL CHEMISTRY
# =========================================================
("CHE001","Glucose","سكر الدم","Clinical Chemistry","SERUM","mg/dL","70-99 fasting"),
("CHE002","Random Blood Glucose","سكر الدم العشوائي","Clinical Chemistry","SERUM","mg/dL","Lab-dependent"),
("CHE003","Urea","اليوريا","Clinical Chemistry","SERUM","mg/dL","15-45"),
("CHE004","Creatinine","الكرياتينين","Clinical Chemistry","SERUM","mg/dL","M: 0.7-1.3; F: 0.6-1.1"),
("CHE005","Uric Acid","حمض اليوريك","Clinical Chemistry","SERUM","mg/dL","M: 3.4-7.0; F: 2.4-6.0"),
("CHE006","Sodium (Na)","الصوديوم","Clinical Chemistry","SERUM","mmol/L","135-145"),
("CHE007","Potassium (K)","البوتاسيوم","Clinical Chemistry","SERUM","mmol/L","3.5-5.1"),
("CHE008","Chloride (Cl)","الكلوريد","Clinical Chemistry","SERUM","mmol/L","98-107"),
("CHE009","Calcium (Ca)","الكالسيوم","Clinical Chemistry","SERUM","mg/dL","8.5-10.5"),
("CHE010","Phosphorus","الفوسفور","Clinical Chemistry","SERUM","mg/dL","2.5-4.5"),
("CHE011","Magnesium","المغنيسيوم","Clinical Chemistry","SERUM","mg/dL","1.7-2.2"),
("CHE012","Total Protein","البروتين الكلي","Clinical Chemistry","SERUM","g/dL","6.0-8.3"),
("CHE013","Albumin","الألبومين","Clinical Chemistry","SERUM","g/dL","3.5-5.0"),
("CHE014","Total Bilirubin","البيليروبين الكلي","Clinical Chemistry","SERUM","mg/dL","0.2-1.2"),
("CHE015","Direct Bilirubin","البيليروبين المباشر","Clinical Chemistry","SERUM","mg/dL","0.0-0.3"),
("CHE016","ALT","ناقلة أمين الألانين","Clinical Chemistry","SERUM","U/L","M: 7-56; F: 7-45"),
("CHE017","AST","ناقلة أمين الأسبارتات","Clinical Chemistry","SERUM","U/L","M: 10-40; F: 9-32"),
("CHE018","ALP","الفوسفاتاز القلوي","Clinical Chemistry","SERUM","U/L","Adult: Lab-dependent"),
("CHE019","GGT","ناقلة غاما غلوتاميل","Clinical Chemistry","SERUM","U/L","Lab-dependent"),
("CHE020","LDH","نازعة هيدروجين اللاكتات","Clinical Chemistry","SERUM","U/L","Lab-dependent"),
("CHE021","Amylase","الأميليز","Clinical Chemistry","SERUM","U/L","Lab-dependent"),
("CHE022","Lipase","الليباز","Clinical Chemistry","SERUM","U/L","Lab-dependent"),
("CHE023","CRP","البروتين المتفاعل C","Clinical Chemistry","SERUM","mg/L","<5"),

# =========================================================
# LIPID PROFILE
# =========================================================
("LIP001","Total Cholesterol","الكوليسترول الكلي","Clinical Chemistry","SERUM","mg/dL","Desirable: <200"),
("LIP002","Triglycerides","الدهون الثلاثية","Clinical Chemistry","SERUM","mg/dL","<150"),
("LIP003","HDL Cholesterol","الكوليسترول عالي الكثافة","Clinical Chemistry","SERUM","mg/dL",">40"),
("LIP004","LDL Cholesterol","الكوليسترول منخفض الكثافة","Clinical Chemistry","SERUM","mg/dL","<100"),
("LIP005","VLDL Cholesterol","الكوليسترول منخفض الكثافة جدًا","Clinical Chemistry","SERUM","mg/dL","5-40"),

# =========================================================
# DIABETES
# =========================================================
("DIA001","Fasting Blood Glucose","سكر الدم الصائم","Clinical Chemistry","SERUM","mg/dL","70-99"),
("DIA002","2-Hour Postprandial Glucose","سكر الدم بعد ساعتين من الأكل","Clinical Chemistry","SERUM","mg/dL","<140"),
("DIA003","HbA1c","السكر التراكمي","Clinical Chemistry","WHOLE_BLOOD","%","<5.7"),
("DIA004","Oral Glucose Tolerance Test (OGTT)","اختبار تحمل الجلوكوز","Clinical Chemistry","SERUM","mg/dL","Lab-dependent"),

# =========================================================
# COAGULATION
# =========================================================
("COA001","Prothrombin Time (PT)","زمن البروثرومبين","Coagulation","PLASMA","sec","Lab-dependent"),
("COA002","INR","النسبة المعيارية الدولية","Coagulation","PLASMA","","0.8-1.2"),
("COA003","Activated Partial Thromboplastin Time (APTT)","زمن الثرومبوبلاستين الجزئي","Coagulation","PLASMA","sec","Lab-dependent"),
("COA004","Fibrinogen","الفيبرينوجين","Coagulation","PLASMA","mg/dL","200-400"),
("COA005","D-Dimer","دي دايمر","Coagulation","PLASMA","mg/L FEU","<0.5"),

# =========================================================
# HORMONES
# =========================================================
("HOR001","TSH","الهرمون المنبه للغدة الدرقية","Hormones","SERUM","µIU/mL","0.4-4.0"),
("HOR002","Free T4 (FT4)","الثيروكسين الحر","Hormones","SERUM","ng/dL","0.8-1.8"),
("HOR003","Free T3 (FT3)","ثلاثي يودوثيرونين الحر","Hormones","SERUM","pg/mL","2.3-4.2"),
("HOR004","FSH","الهرمون المنبه للجريبات","Hormones","SERUM","mIU/mL","Cycle-dependent"),
("HOR005","LH","الهرمون اللوتيني","Hormones","SERUM","mIU/mL","Cycle-dependent"),
("HOR006","Prolactin","البرولاكتين","Hormones","SERUM","ng/mL","Sex-dependent"),
("HOR007","Estradiol (E2)","الإستراديول","Hormones","SERUM","pg/mL","Cycle-dependent"),
("HOR008","Progesterone","البروجسترون","Hormones","SERUM","ng/mL","Cycle-dependent"),
("HOR009","Testosterone","التستوستيرون","Hormones","SERUM","ng/dL","Sex-dependent"),
("HOR010","Cortisol","الكورتيزول","Hormones","SERUM","µg/dL","Time-dependent"),
("HOR011","Vitamin D (25-OH)","فيتامين د","Hormones","SERUM","ng/mL","30-100"),
("HOR012","Vitamin B12","فيتامين ب12","Hormones","SERUM","pg/mL","200-900"),
("HOR013","Ferritin","الفيريتين","Hormones","SERUM","ng/mL","Sex-dependent"),

# =========================================================
# SEROLOGY / IMMUNOLOGY
# =========================================================
("SER001","C-Reactive Protein (CRP)","البروتين المتفاعل C","Serology & Immunology","SERUM","mg/L","<5"),
("SER002","ASO","مضاد الستربتوليزين O","Serology & Immunology","SERUM","IU/mL","<200"),
("SER003","Rheumatoid Factor (RF)","عامل الروماتويد","Serology & Immunology","SERUM","IU/mL","<20"),
("SER004","Widal Test","اختبار ويدال","Serology & Immunology","SERUM","","Lab-dependent"),
("SER005","Brucella Agglutination Test","اختبار البروسيلا","Serology & Immunology","SERUM","","Lab-dependent"),
("SER006","ANA","الأجسام المضادة للنواة","Serology & Immunology","SERUM","","Negative"),
("SER007","Anti-dsDNA","أجسام مضادة للحمض النووي مزدوج السلسلة","Serology & Immunology","SERUM","IU/mL","Lab-dependent"),
("SER008","Complement C3","المتممة C3","Serology & Immunology","SERUM","mg/dL","90-180"),
("SER009","Complement C4","المتممة C4","Serology & Immunology","SERUM","mg/dL","10-40"),
("SER010","Total IgE","الغلوبيولين المناعي E الكلي","Serology & Immunology","SERUM","IU/mL","Age-dependent"),

# =========================================================
# VIRAL SEROLOGY
# =========================================================
("VIR001","HBsAg","مستضد سطح التهاب الكبد B","Virology","SERUM","","Negative"),
("VIR002","Anti-HBs","الأجسام المضادة لسطح التهاب الكبد B","Virology","SERUM","mIU/mL","Lab-dependent"),
("VIR003","Anti-HBc Total","الأجسام المضادة الكلية لنواة التهاب الكبد B","Virology","SERUM","","Negative"),
("VIR004","HBeAg","مستضد e لالتهاب الكبد B","Virology","SERUM","","Negative"),
("VIR005","Anti-HCV","الأجسام المضادة لالتهاب الكبد C","Virology","SERUM","","Negative"),
("VIR006","HIV 1/2 Ag/Ab","مستضد/أجسام مضادة HIV 1/2","Virology","SERUM","","Non-reactive"),
("VIR007","HAV IgM","الأجسام المضادة IgM لالتهاب الكبد A","Virology","SERUM","","Negative"),
("VIR008","HAV IgG","الأجسام المضادة IgG لالتهاب الكبد A","Virology","SERUM","","Negative"),
("VIR009","CMV IgM","الأجسام المضادة IgM للفيروس المضخم للخلايا","Virology","SERUM","","Negative"),
("VIR010","CMV IgG","الأجسام المضادة IgG للفيروس المضخم للخلايا","Virology","SERUM","","Negative"),
("VIR011","Rubella IgM","الأجسام المضادة IgM للحصبة الألمانية","Virology","SERUM","","Negative"),
("VIR012","Rubella IgG","الأجسام المضادة IgG للحصبة الألمانية","Virology","SERUM","","Negative"),
("VIR013","EBV VCA IgM","الأجسام المضادة IgM لـ EBV VCA","Virology","SERUM","","Negative"),
("VIR014","EBV VCA IgG","الأجسام المضادة IgG لـ EBV VCA","Virology","SERUM","","Negative"),

# =========================================================
# URINALYSIS
# =========================================================
("URI001","Urinalysis","تحليل البول الكامل","Urinalysis","URINE","","Lab-dependent"),
("URI002","Urine Protein","بروتين البول","Urinalysis","URINE","","Negative"),
("URI003","Urine Glucose","جلوكوز البول","Urinalysis","URINE","","Negative"),
("URI004","Urine Ketones","كيتونات البول","Urinalysis","URINE","","Negative"),
("URI005","Urine Blood","دم في البول","Urinalysis","URINE","","Negative"),
("URI006","Urine Bilirubin","بيليروبين البول","Urinalysis","URINE","","Negative"),
("URI007","Urine Nitrite","نيتريت البول","Urinalysis","URINE","","Negative"),
("URI008","Urine Leukocyte Esterase","إنزيم كريات الدم البيضاء في البول","Urinalysis","URINE","","Negative"),

# =========================================================
# PARASITOLOGY
# =========================================================
("PAR001","Stool Routine Examination","فحص البراز الروتيني","Parasitology","STOOL","","No parasites"),
("PAR002","Occult Blood in Stool","الدم الخفي في البراز","Parasitology","STOOL","","Negative"),
("PAR003","Giardia Antigen","مستضد الجيارديا","Parasitology","STOOL","","Negative"),
("PAR004","Entamoeba histolytica Antigen","مستضد الأميبا الحالة للنسج","Parasitology","STOOL","","Negative"),
("PAR005","Cryptosporidium Antigen","مستضد الكريبتوسبوريديوم","Parasitology","STOOL","","Negative"),
("PAR006","Malaria Blood Film","لطاخة دم للملاريا","Parasitology","WHOLE_BLOOD","","No Plasmodium seen"),

# =========================================================
# MICROBIOLOGY
# =========================================================
("MIC001","Urine Culture","مزرعة البول","Microbiology","URINE","","No significant growth"),
("MIC002","Stool Culture","مزرعة البراز","Microbiology","STOOL","","No pathogenic growth"),
("MIC003","Blood Culture","مزرعة الدم","Microbiology","WHOLE_BLOOD","","No growth"),
("MIC004","Sputum Culture","مزرعة البلغم","Microbiology","OTHER","","No significant growth"),
("MIC005","Wound Swab Culture","مزرعة مسحة الجرح","Microbiology","SWAB","","No significant growth"),
("MIC006","Throat Swab Culture","مزرعة مسحة الحلق","Microbiology","SWAB","","No significant growth"),

# =========================================================
# MYCOLOGY
# =========================================================
("MYC001","KOH Preparation","فحص KOH للفطريات","Mycology","SWAB","","No fungal elements"),
("MYC002","Fungal Culture","مزرعة فطرية","Mycology","OTHER","","No fungal growth"),

# =========================================================
# TUMOR MARKERS
# =========================================================
("TUM001","PSA","المستضد النوعي للبروستاتا","Tumor Markers","SERUM","ng/mL","Age-dependent"),
("TUM002","Free PSA","PSA الحر","Tumor Markers","SERUM","ng/mL","Lab-dependent"),
("TUM003","AFP","ألفا فيتو بروتين","Tumor Markers","SERUM","ng/mL","Lab-dependent"),
("TUM004","CEA","المستضد السرطاني الجنيني","Tumor Markers","SERUM","ng/mL","Lab-dependent"),
("TUM005","CA 125","المستضد السرطاني 125","Tumor Markers","SERUM","U/mL","<35"),
("TUM006","CA 19-9","المستضد السرطاني 19-9","Tumor Markers","SERUM","U/mL","<37"),
("TUM007","CA 15-3","المستضد السرطاني 15-3","Tumor Markers","SERUM","U/mL","<30"),

# =========================================================
# BLOOD BANK
# =========================================================
("BB001","ABO Blood Group","فصيلة الدم ABO","Blood Bank","WHOLE_BLOOD","","A/B/AB/O"),
("BB002","Rh(D) Typing","عامل Rh(D)","Blood Bank","WHOLE_BLOOD","","Positive/Negative"),
("BB003","Direct Coombs Test (DAT)","اختبار كومبس المباشر","Blood Bank","WHOLE_BLOOD","","Negative"),
("BB004","Indirect Coombs Test (IAT)","اختبار كومبس غير المباشر","Blood Bank","SERUM","","Negative"),
("BB005","Crossmatch","اختبار التوافق","Blood Bank","SERUM","","Compatible"),

# =========================================================
# MOLECULAR
# =========================================================
("MOL001","HBV DNA PCR","PCR للحمض النووي لفيروس التهاب الكبد B","Molecular Diagnostics","PLASMA","IU/mL","Detected/Not detected"),
("MOL002","HCV RNA PCR","PCR للحمض النووي الريبي لفيروس التهاب الكبد C","Molecular Diagnostics","PLASMA","IU/mL","Detected/Not detected"),
("MOL003","HIV RNA PCR","PCR لفيروس HIV","Molecular Diagnostics","PLASMA","copies/mL","Detected/Not detected"),
("MOL004","COVID-19 PCR","PCR لفيروس SARS-CoV-2","Molecular Diagnostics","SWAB","","Detected/Not detected"),

]


class Command(BaseCommand):
    help = "Seed standard laboratory tests"

    def handle(self, *args, **options):

        departments = {
            d.name_en: d
            for d in Department.objects.filter(is_active=True)
        }

        created = 0
        updated = 0
        skipped = 0

        for (
            code,
            name_en,
            name_ar,
            department_name,
            sample_type,
            unit,
            reference_range,
        ) in TESTS:

            department = departments.get(department_name)

            if not department:
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipped {code}: department '{department_name}' not found."
                    )
                )
                skipped += 1
                continue

            test, was_created = LaboratoryTest.objects.update_or_create(
                code=code,
                defaults={
                    "name_en": name_en,
                    "name_ar": name_ar,
                    "department": department,
                    "sample_type": sample_type,
                    "unit": unit,
                    "reference_range": reference_range,
                    "is_active": True,
                },
            )

            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Laboratory seed completed: created={created}, "
                f"updated={updated}, skipped={skipped}"
            )
        )
