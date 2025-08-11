from django.core.exceptions import BadRequest
from django.contrib.auth.models import User
from datetime import datetime
from docx import Document
from PIL import Image
import numpy as np
import re, json



class Validation:
    @staticmethod
    def validate_object(model, object_id):
        try:
            return model.objects.get(id=object_id)
        except:
            raise BadRequest("Object not found - " + str(model))
        
    @staticmethod
    def validate_many_objects(model, objects_ids):
        for object_id in objects_ids:
            try:
                model.objects.get(id=object_id)
            except:
                raise BadRequest("Object not found - " + str(model))
        return objects_ids

    @staticmethod
    def validate_first_last_name(name):
        if not name:
            raise BadRequest("no name found")
        
        if len(name) > 50:
            raise BadRequest("no name more than 50")
                
        pattern = r'^[a-zA-Z ,.\'-]+$'
        if not re.match(pattern, name):
            raise BadRequest("bad pattern")
        
        return name
    
    @staticmethod
    def validate_name(name):
        if not name:
            raise BadRequest("Name is empty")
        elif len(name) > 255:
            raise BadRequest("Name more than 255 characters")
        return name

    @staticmethod
    def validate_date(date):
        try:
            datetime.strptime(date, '%Y-%m-%d')
            return date
        except ValueError:
            raise BadRequest("Invalid date format.")

    @staticmethod
    def validate_users(user_ids):
        for user_id in user_ids:
            try:
                User.objects.get(id=user_id)
            except:
                raise BadRequest("user not found")
        return user_ids

    @staticmethod
    def validate_phoneNumber(phoneNumber):
        if not phoneNumber:
            raise BadRequest("user phone number")

        pattern = r'^\+(9[976]\d|8[987530]\d|6[987]\d|5[90]\d|42\d|3[875]\d|2[98654321]\d|9[8543210]|8[6421]|6[6543210]|5[87654321]|4[987654310]|3[9643210]|2[70]|7|1)\d{1,14}$'
        if not re.match(pattern, phoneNumber):
            raise BadRequest("not correct pattern")
        return phoneNumber
    
    @staticmethod
    def validate_notRequired_phoneNumber(phoneNumber):
        if phoneNumber:
            pattern = r'^\+(9[976]\d|8[987530]\d|6[987]\d|5[90]\d|42\d|3[875]\d|2[98654321]\d|9[8543210]|8[6421]|6[6543210]|5[87654321]|4[987654310]|3[9643210]|2[70]|7|1)\d{1,14}$'
            if not re.match(pattern, phoneNumber):
                raise BadRequest("not correct pattern")
            return phoneNumber
        return phoneNumber

    @staticmethod
    def validate_email(email):
        if not email:
            raise BadRequest("No email address")
        
        if len(email) > 50:
            raise BadRequest("To long of email address")
        
        pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(pattern, email):
            raise BadRequest("Invalid email address pattern")

        return email
    
    @staticmethod
    def validate_notRequired_email(email):
        if email:
            if len(email) > 50:
                raise BadRequest("To long of email address")
            
            pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            if not re.match(pattern, email):
                raise BadRequest("Invalid email address")
        return email
    
    @staticmethod
    def validate_docxFile(file):
        if not file:
            raise BadRequest("File is empty")
        
        if file.size > 20 * 1024 * 1024:
            raise BadRequest("File size exceeds 20 megabytes")
        
        try :
            Document(file)
        except:
            raise BadRequest("Invalid file")
        
        return file
    
    @staticmethod
    def validate_notRequired_docxFile(file):
        if file:
            if file.size > 20 * 1024 * 1024:
                raise BadRequest("File size exceeds 20 megabytes")
            
            try :
                Document(file)
            except:
                raise BadRequest("Invalid file")
        return file
    
    @staticmethod
    def validate_vuln_status(status):
        vuln_statuses = ['Unresolved', "Resolved"]
        if status in vuln_statuses:
            return status
        else:
            raise BadRequest("Unrecoginized Vulnerabilty status")
        
    @staticmethod
    def validate_cvss(cvss):
        if cvss=='':
            return cvss
        try:
            cvss=float(cvss)
            if cvss<0 or cvss>10:
                raise BadRequest("Invalid cvss")
            return cvss
        except:
            raise BadRequest("Invalid cvss")
        
    @staticmethod
    def validate_risk_rating(risk_rating):
        valid_ratings = ["Critical", "High", "Medium", "Low",""]
        if risk_rating not in valid_ratings:
            raise BadRequest("invalid risk rating")
        return risk_rating
    
    @staticmethod
    def validate_image(image):
        # proper image types
        image_types = ['image/png', 'image/jpg', 'image/jpeg']
        if image.content_type not in image_types:
            raise BadRequest("Invalid image type")
        
        # open image and validate
        try :
            Image.open(image.file)
        except:
            raise BadRequest("Invalid file")
        
        # Image size must be less than 2 mega bystes
        max_size_bytes = 2 * 1024 * 1024  
        if len(image.read()) > max_size_bytes:
            raise BadRequest("Image size exceeds the allowed limit of 2 MB")

        return image
    
    @staticmethod
    def validate_password(password):
        password_regex = r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*()_+|~\-=`{}[\]:";\'<>?,./])\S{8,}$'
        
        if not password:
            raise BadRequest("Password is empty")

        if not re.match(password_regex, password):
            raise BadRequest("Invalid password")
            
        return password

    
    @staticmethod
    def validate_username(username):
        if not username:
            raise BadRequest("Username is empty")
        if " " in username:
            raise BadRequest("Username has spaces")
        
        if any(char.isupper() for char in username):
            raise BadRequest("There are upper cases")
        
        if not re.match(r'^(?=[a-zA-Z0-9._]{2,40}$)(?!.*[_.]{2})[^_.].*[^_.]$', username):
            raise BadRequest("Invalid username format")
        
        if User.objects.filter(username=username).exists():
            raise BadRequest("Username already exists")
        return username
    
    @staticmethod
    def validate_editedUsername(username, old_username):
        if not username:
            raise BadRequest("Username is empty")
        
        if " " in username:
            raise BadRequest("Username has spaces")
        
        if any(char.isupper() for char in username):
            raise BadRequest("There are upper cases")
        
        if not re.match(r'^(?=[a-zA-Z0-9._]{2,40}$)(?!.*[_.]{2})[^_.].*[^_.]$', username):
            raise BadRequest("Invalid username format")
        
        if username != old_username and User.objects.filter(username=username).exists():
            raise BadRequest("Username already exists")
        return username
    
    @staticmethod
    def validate_color(color):
        hex_color_pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{8})$'
        if not color:
            raise BadRequest("Color is empty")
        if not re.match(hex_color_pattern, color):
            raise BadRequest("Invalid color")
        return color
    
    @staticmethod
    def validate_permissions(model, permissions):
        for permission in permissions:
            if permission:
                try:
                    model.objects.get(name=permission)
                except:
                    raise BadRequest("Permission not found")
        return permissions
           
    @staticmethod
    def validate_permission(model, permission):
        if permission:
            try:
                model.objects.get(name=permission)
            except:
                raise BadRequest("Permission not found")
        return permission
    
    @staticmethod
    def validate_unique_name(model, name):
        if not name:
            raise BadRequest("Name is empty")
        if model.objects.filter(name=name).exists():
            raise BadRequest("Name already exists")
        return name
    
    @staticmethod
    def validate_edited_unique_name(model, name, old_name):
        if not name:
            raise BadRequest("Name is empty")
        if name != old_name and model.objects.filter(name=name).exists():
            raise BadRequest("Name already exists")
        return name
    
        
    @staticmethod 
    def validate_json(json_input):
        if not json_input:
            raise BadRequest("Json is empty")
        else:
            try:
                tmp = json.loads(json_input)
            except:
                raise BadRequest("Invalid json")
        return json_input