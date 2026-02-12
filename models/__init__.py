from .base import Base
from .base import BaseModel

# ЭКСПОРТИРУЕМ ТОЛЬКО User!
from .user import User

# НИЧЕГО БОЛЬШЕ НЕ ЭКСПОРТИРУЕМ!
# from .patient import Patient
# from .doctor import Doctor
# from .appointment import Appointment
# from .diagnosis import Diagnosis, PatientDiagnosis
# from .measurement import Measurement
# from .prescription import Prescription
# from .complaint import Complaint