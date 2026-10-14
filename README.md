# HospitalSystem — HIS / LIS

نظام إدارة مستشفى متكامل HIS / LIS مبني باستخدام Django.

## الوحدات الرئيسية

- الاستقبال والمرضى
- المختبر LIS
- الأشعة
- الصيدلية
- التمريض
- الطوارئ
- التنويم
- العمليات
- بنك الدم
- الفوترة
- المخزون
- الأطباء والمستخدمون والصلاحيات

## الأدوار الرئيسية

- ADMIN
- MANAGER
- DOCTOR
- LAB
- RADIOLOGY
- PHARMACY
- NURSING
- SURGERY
- BLOOD_BANK
- BILLING
- INVENTORY
- RECEPTION
- EMERGENCY
- INPATIENT

يمكن تخصيص الصلاحيات حسب الدور والمستخدم والقسم.

## نظام الصلاحيات

يعتمد النظام على صلاحيات دقيقة Granular Permissions.

أمثلة:

radiology.view
radiology.orders.view
radiology.orders.create
radiology.results.enter
radiology.results.edit

الصلاحية العامة لا تعني بالضرورة السماح بكل العمليات داخل القسم.


## دورة عمل المختبر

القسم الطبي
↓
طلب الفحص
↓
المختبر
↓
استقبال الطلب
↓
سحب العينة
↓
معالجة العينة
↓
إدخال النتائج
↓
مراجعة النتيجة
↓
إكمال الطلب
↓
إرجاع النتيجة للقسم

حالات طلب المختبر:

REQUESTED
RECEIVED
COLLECTED
PROCESSING
COMPLETED
CANCELLED

الأولويات:

NORMAL
URGENT
STAT

## التقنيات المستخدمة

- Python
- Django 6.x
- SQLite
- Django Templates
- Django Authentication
- Django Middleware
- HTML5
- CSS3
- JavaScript
- Bootstrap
- ReportLab
- PDF generation

## هيكل المشروع

HospitalSystem/
├── accounts/
├── departments/
├── patients/
├── doctors/
├── laboratory/
├── radiology/
├── pharmacy/
├── nursing/
├── emergency/
├── inpatient/
├── surgery/
├── blood_bank/
├── billing/
├── inventory/
├── reception/
├── reports/
├── system_settings/
├── config/
├── templates/
├── static/
├── media/
├── db.sqlite3
└── manage.py


## تشغيل النظام

من داخل مجلد المشروع:

cd ~/storage/downloads/HospitalSystem_backup

فحص النظام:

python manage.py check

تشغيل الخادم:

python manage.py runserver 0.0.0.0:8000

ثم افتح:

http://127.0.0.1:8000/

## تشغيل النظام على Android / Termux

المسار الحالي:

~/storage/downloads/HospitalSystem_backup

تفعيل البيئة الافتراضية:

source ~/HospitalSystem_backup_venv/bin/activate

ثم:

cd ~/storage/downloads/HospitalSystem_backup
python manage.py check
python manage.py runserver 0.0.0.0:8000

## قاعدة البيانات

قاعدة البيانات الحالية:

db.sqlite3

يجب الحفاظ على قاعدة البيانات وعدم حذفها أو استبدالها أثناء التطوير.

### إنشاء نسخة احتياطية

قبل أي تعديل مهم:

cd ~/storage/downloads/HospitalSystem_backup

cp db.sqlite3 "db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)"

## التطوير الآمن

قبل أي تعديل مهم:

1. فحص النظام الحالي.
2. قراءة الملفات المتعلقة بالتعديل.
3. إنشاء Backup عند الحاجة.
4. تنفيذ تعديل محدود.
5. تشغيل فحص Django.
6. اختبار الوظيفة.
7. اختبار الصلاحيات.
8. مراجعة النتيجة.

أوامر الفحص الأساسية:

python manage.py check

python manage.py showmigrations

python manage.py makemigrations --check

لا يتم تشغيل migrations جديدة على قاعدة البيانات الحالية دون مراجعة مسبقة.


## الأمان والصلاحيات

يستخدم النظام Middleware للتحقق من صلاحيات المستخدم حسب:

- المستخدم.
- الدور.
- القسم.
- التطبيق.
- العملية المطلوبة.

أمثلة على الصلاحيات:

radiology.orders.create
radiology.orders.status
radiology.results.enter
radiology.results.edit

pharmacy.prescriptions.create
pharmacy.prescriptions.edit

nursing.assessment.create
nursing.medications.create
nursing.care_plan.create

surgery.status
surgery.procedures.create
surgery.team.create
surgery.postoperative_notes.create

blood_bank.donors.create
blood_bank.donors.edit
blood_bank.units.create
blood_bank.requests.create
blood_bank.crossmatch
blood_bank.transfusion

billing.items.create
billing.items.delete
billing.status

## اختبارات الصلاحيات

تم اختبار نظام الصلاحيات على المستخدمين الموجودين في قاعدة البيانات.

النتيجة:

ACTIVE USERS TESTED : 33
PERMISSION CASES    : 143
TEST ERRORS         : 0

كما تم اختبار Middleware فعليًا على مسارات مسموحة وممنوعة.

النتيجة النهائية:

FINAL REAL MIDDLEWARE ALLOW/DENY TEST
TEST ERRORS: 0
FINAL REAL MIDDLEWARE TEST PASSED

## قواعد مهمة للمطورين

### الحفاظ على البيانات

لا يتم حذف قاعدة البيانات الحالية أو إعادة إنشائها دون موافقة صريحة.

### Seed Commands

لا يتم تشغيل أوامر Seed على قاعدة البيانات الحالية دون مراجعة.

ومنها:

seed_departments
seed_lab_tests

### ملفات الترقية

لا يتم تشغيل:

apply_his_upgrade.py

دون مراجعة واختبار مسبق.

### ملفات الصلاحيات

أي تعديل على:

accounts/permissions.py
accounts/middleware.py

يجب أن يتبعه فحص واختبار كامل للصلاحيات.

## GitHub

المستودع:

https://github.com/MogahidAlmohia/HospitalSystem

الفرع الرئيسي:

main

## منهجية التطوير

1. فحص النظام.
2. تحديد المشكلة.
3. أخذ Backup.
4. تعديل محدود.
5. فحص Syntax.
6. Django check.
7. اختبار الوظيفة.
8. اختبار الصلاحيات.
9. اختبار المسارات.
10. مراجعة النتيجة.
11. حفظ التغيير.

الهدف هو إضافة الميزات مع المحافظة على البيانات والوظائف الموجودة.

## التطوير المستقبلي

يمكن تطوير النظام مستقبلًا ليشمل:

- REST API.
- تطبيق Android / iOS.
- PostgreSQL.
- لوحات معلومات متقدمة.
- إشعارات.
- تكامل أجهزة المختبر.
- HL7 / FHIR.
- العمل Online / Offline.
- إدارة فروع متعددة.
- تقارير إحصائية متقدمة.

## حالة المشروع

المشروع في مرحلة تطوير مستمرة.

الوحدات الأساسية موجودة، ويتم تطوير وتحسين:

- الواجهات.
- الصلاحيات.
- المختبر.
- الأشعة.
- الصيدلية.
- التمريض.
- بنك الدم.
- الفوترة.
- المخزون.
- التقارير.
- التكامل بين الأقسام.

## الترخيص

يتم تحديد سياسة الترخيص والاستخدام النهائي للمشروع لاحقًا وفق متطلبات المشروع والجهة المالكة.

## المطور

HospitalSystem — HIS / LIS

نظام إدارة معلومات المستشفى والمختبر.

