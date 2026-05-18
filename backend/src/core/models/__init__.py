# Importa todos os models para que Base.metadata os registre antes do create_all
from core.models.patient import Patient
from core.models.doctor import Doctor
from core.models.appointment import Appointment, AppointmentStatus

__all__ = ["Patient", "Doctor", "Appointment", "AppointmentStatus"]
