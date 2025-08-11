from azure.storage.blob import BlobServiceClient, ContentSettings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from assessments.models import CKImageUpload
from django.template import Template as T
from django.template import Context as C
from django.http import JsonResponse
from .validations import Validation
from django.conf import settings
from bs4 import BeautifulSoup
from cvss import CVSS3
from PIL import Image
import os, io, PIL, sys, boto3

@login_required
def calculate_cvss_31(request):
    if request.method == 'GET':
        try:
            av = request.GET.get('AV')
            ac = request.GET.get('AC')
            pr = request.GET.get('PR')
            ui = request.GET.get('UI')
            s = request.GET.get('S')
            c = request.GET.get('C')
            i = request.GET.get('I')
            a = request.GET.get('A')
            cvss_vector = f"CVSS:3.1/AV:{av}/AC:{ac}/PR:{pr}/UI:{ui}/S:{s}/C:{c}/I:{i}/A:{a}"

            cvss3 = CVSS3(cvss_vector)
            score = list(cvss3.scores())
            return JsonResponse({'base_score': score[0],  
                                 'temporal_score': score[1],  
                                 'environmental_score': score[2],
                                 'results_url': "https://www.first.org/cvss/calculator/3.1#" + str(cvss_vector)                
                                 },status=200)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
@login_required
def upload_ck_image(request):
    ''' This function takes an image and a name of the model and the 
    id of that model this will later help me in reporting '''
    
    if request.method == 'POST' and request.FILES.get('upload'):
        image_file = Validation.validate_image(request.FILES['upload'])
        
        for_model = request.POST.get('for_model')
        model_id = request.POST.get('model_id')

        new_image = CKImageUpload.objects.create(image=image_file,
                                                    for_model = for_model,
                                                    model_id = int(model_id))
        
        # image_url = "http://127.0.0.1:8000" + new_image.image.url
        image_url = new_image.image.url
        
        return JsonResponse({'url': image_url})
    else:
        return JsonResponse({'error': 'Image upload failed.'}, status=400)



def render_short_codes(html_to_render, context):
    s_modified_dict = {}
    if context["s_fields"].items():
        for key, value in context["s_fields"].items():
            soup = BeautifulSoup(value, 'html.parser')
            new_text_value = soup.get_text()
            s_modified_dict[key] = new_text_value
    context["s_fields"] = s_modified_dict
    
    a_modified_dict = {}
    if context["a_fields"].items():
        for key, value in context["a_fields"].items():
            soup = BeautifulSoup(value, 'html.parser')
            new_text_value = soup.get_text()
            a_modified_dict[key] = new_text_value
    context["a_fields"] = a_modified_dict
    
    html_to_render = T(str(html_to_render))
    context = C(context)
    rendered_html = html_to_render.render(context)
    return rendered_html


def resize_image(image, image_name, width, length):
    img_io = io.BytesIO()
    img = Image.open(image)
    img = img.resize((width, length))

    img.save(img_io, format="JPEG")
            #InMemoryUploadedFile(file, field_name, name, content_type, size, charset)
    new_pic= InMemoryUploadedFile(img_io, 'ImageField', str(image_name) + '.jpeg', 'JPEG', sys.getsizeof(img_io), None)

    return new_pic

def update_image_metadata(file_name):
    if settings.MEDIA_STORAGE_TYPE == 'S3':
        s3 = boto3.resource('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, endpoint_url=settings.AWS_S3_ENDPOINT_URL)

        s3_object = s3.Object(settings.AWS_STORAGE_BUCKET_NAME, file_name)
        s3_object.metadata.update({'Content-Disposition': 'attachment'})
        
        s3_object.copy_from(
            CopySource={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': file_name},
            Metadata=s3_object.metadata,
            MetadataDirective='REPLACE'
        )
        
    elif settings.MEDIA_STORAGE_TYPE == 'BLOB':
        blob_service_client = BlobServiceClient(account_url='https://' + settings.AZURE_CUSTOM_DOMAIN, credential=settings.AZURE_ACCOUNT_KEY)
        blob_client = blob_service_client.get_blob_client(container=settings.AZURE_CONTAINER, blob=file_name)
        
        properties = blob_client.get_blob_properties()
        blob_headers = ContentSettings(content_type="text/farouk",
                                    content_encoding=properties.content_settings.content_encoding,
                                    content_language="en-US",
                                    content_disposition='attachment',
                                    cache_control=properties.content_settings.cache_control,
                                    content_md5=properties.content_settings.content_md5)
        blob_client.set_http_headers(blob_headers)
    