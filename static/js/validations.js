// This Validation Script is to handel validation in a organized Manner. To get to work:

// 1. give the form an id of "validateForm"
// 2. on the input/select tags add the needed valiadation classes listed below
// 3. add the span tag for the validation message and give it an id of <input-tage-name>-validation-message
//                      Example: <span class="validation-message" id="client-validation-message"></span>


// Below are the list of avaliable classess
// validate-required :: makes sure that the filed is selected
// validate-email :: makes sure that the email is writen corectly
// validate-phone :: makes sure that the phone is writen corectly
// validate-first-last-name :: makes sure that the names of the users are correct
// validate-password :: makes sure password meets the requirements

// validate-file-size-20 :: makes sure that the file uploaded is less than 20 mg
// validate-file-docx :: makes sure that the file uploaded is a document and less than 20 mg
// validate-file-image :: makes sure that the file uploaded is a image and less than 2 mg


class FormValidator {
    constructor(form) {
        this.form = form;
        this.form.addEventListener('submit', this.validate.bind(this));
    }

    async validate(e) {
        e.preventDefault();

        const elements = this.form.elements;
        const validationMessages = [];

        // ------------------ 1. Main Loop Over Elments Classes ------------------
        for (let i = 0; i < elements.length; i++) {
            const element = elements[i];

            if(element.classList.contains('validate-required')){
                if (element.type === 'checkbox') {
                    const checkboxes = document.querySelectorAll(`input[type="checkbox"][name="${element.name}"]`);
                    if (!Array.from(checkboxes).some(checkbox => checkbox.checked)) {
                        this.handleValidationFailure(element, `${element.name}-validation-message`, 'At least one user is required');
                        validationMessages.push('At least one user is required');
                    } else {
                        this.handleValidationSuccess(element, `${element.name}-validation-message`);
                    }
                
                } else if (element.value.trim() === '' || element.value.trim() === '0') {
                    this.handleValidationFailure(element, `${element.name}-validation-message`, 'This field is required');
                    validationMessages.push('This field is required');
                } else {
                    this.handleValidationSuccess(element, `${element.name}-validation-message`);
                }
            }
                
            if(element.classList.contains('validate-email')){
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                
                if (element.value.trim() != '' ){
                    if (!emailRegex.test(element.value) && !element.value.length <= 50) {
                        this.handleValidationFailure(element, `${element.name}-validation-message`, 'Invalid email format');
                        validationMessages.push('Invalid email format');
                    }
                    else {
                        this.handleValidationSuccess(element, `${element.name}-validation-message`);
                    }
                }
                
            }

            if(element.classList.contains('validate-phone')){
                const phoneRegex = /^\+(9[976]\d|8[987530]\d|6[987]\d|5[90]\d|4[987654310]\d|3[875]\d|2[98654321]\d|9[8543210]|8[6421]|6[6543210]|5[87654321]|4[987654310]|3[9643210]|2[70]|7|1)\d{1,14}$/;
                
                if (element.value.trim() != '' ){
                    if (!phoneRegex.test(element.value)) {
                        this.handleValidationFailure(element, `${element.name}-validation-message`, 'Invalid phone format (Ex: +201012345678)');
                        validationMessages.push('Invalid phone format (Ex: +201012345678)');
                    }
                    else {
                        this.handleValidationSuccess(element, `${element.name}-validation-message`);
                    }
                }
            }            

            if(element.classList.contains('validate-first-last-name')){
                const nameRegex = /^[a-zA-Z ,.'-]+$/;
                
                if (element.value.trim() != '' ){
                    if (!nameRegex.test(element.value) && !element.value.length <= 50) {
                        this.handleValidationFailure(element, `${element.name}-validation-message`, 'Invalid name format');
                        validationMessages.push('Invalid name format');
                    }
                    else {
                        this.handleValidationSuccess(element, `${element.name}-validation-message`);
                    }
                }
                
            }
                  
            if (element.classList.contains('validate-password')) {
                if (element.value.trim() != ''){    
                    const errorMessage = this.validatePassword(element.value.trim());
                    if (errorMessage) {
                        this.handleValidationFailure(element, `${element.name}-validation-message`, errorMessage);
                        validationMessages.push(errorMessage);
                    } else {
                        this.handleValidationSuccess(element, `${element.name}-validation-message`);
                    }
                }
            }

            if(element.classList.contains('validate-file-size-20')){
                if (element.files[0]){
                    if (element.files[0].size > 20 * 1024 * 1024 ) {
                        this.handleValidationFailure(element, `${element.name}-validation-message`, 'File size exceeds the allowed limit of 20 MB');
                        validationMessages.push('File size exceeds the allowed limit of 20 MB');
                    }  
                    else {
                        this.handleValidationSuccess(element, `${element.name}-validation-message`);
                    }
                }
            }
            
            if(element.classList.contains('validate-file-docx')){
                if (element.files[0]){
                    if (element.files[0].size > 20 * 1024 * 1024 ) {
                        this.handleValidationFailure(element, `${element.name}-validation-message`, 'File size exceeds the allowed limit of 20 MB');
                        validationMessages.push('File size exceeds the allowed limit of 20 MB');
                    }  
                    if (element.files[0].type !== "application/vnd.openxmlformats-officedocument.wordprocessingml.document") {
                        this.handleValidationFailure(element, `${element.name}-validation-message`, 'Template file must be .docx');
                        validationMessages.push('Template must be .docx');
                    }
                    else {
                        this.handleValidationSuccess(element, `${element.name}-validation-message`);
                    }
                }
            }

            if(element.classList.contains('validate-file-image')){
                if (element.files[0]){
                    const imageRegex = /([a-zA-Z0-9\s_\\.\-\(\):])+(.jpg|.png|.jpeg)$/;

                    if (element.files[0].size > 2 * 1024 * 1024 ) {
                        this.handleValidationFailure(element, `${element.name}-validation-message`, 'Image size exceeds the allowed limit of 2 MB');
                        validationMessages.push('Image size exceeds the allowed limit of 2 MB');
                    }  
                    else if (!imageRegex.test(element.value.toLowerCase())) {
                        this.handleValidationFailure(element, `${element.name}-validation-message`, 'Image file must be .jpg or .jpeg or .png');
                        validationMessages.push('Image file must be .jpg or .jpeg or .png');
                    }
                    else {
                        this.handleValidationSuccess(element, `${element.name}-validation-message`);
                    }
                }
            }

            if(element.classList.contains('validate-json')){                
                if (element.value.trim() != '' ){
                    try {
                        JSON.parse(element.value);
                        this.handleValidationSuccess(element, `${element.name}-validation-message`);
                    
                    } catch (error) {
                        this.handleValidationFailure(element, `${element.name}-validation-message`, 'Invalid json format');
                        validationMessages.push('Invalid json format');
                    }
                }
            }
        }

        // ------------------ 2. More Custom Validations ------------------

        // --> start date > end date (Assessments add/edit page)
        const start_date = document.getElementById("start_date_custom");
        const end_date = document.getElementById("end_date_custom");
        if (start_date && end_date) {
            if(new Date(start_date.value) > new Date(end_date.value) ){
                start_date.classList.add("is-invalid");
                end_date.classList.add("is-invalid");
                const errorContainer = document.getElementById("start_date-validation-message");
                errorContainer.textContent ="Start date must be before end date";
                validationMessages.push("Start date must be before end date");
            }
        }
        
        // --> Validate Username
        const username = document.getElementById("username_custom");
        if (username && username.value.trim() != '') {
            const usernameRegex = /^(?=[a-z0-9._]{2,40}$)(?!.*[_.]{2})[^_.].*[^_.]$/;
            if (!usernameRegex.test(username.value)) {
                this.handleValidationFailure(username, `${username.name}-validation-message`, 'Invalid username format: no upercase letters are allowed. can only contain _ .');
                validationMessages.push("Invalid username format: no upercase letters are allowed. can only contain _ .");
            } else {
                if (username.value !== originalUsername){
                    try {
                        const isAvailable = await check_name_availability('user', username.value);
                        if (!isAvailable) {
                            username.classList.add("is-invalid");
                            const errorContainer = document.getElementById("username-validation-message");
                            errorContainer.textContent = "Username is already taken";
                            validationMessages.push("Username is already taken");
                        } else {
                            username.classList.remove('is-invalid');
                            const errorContainer = document.getElementById("username-validation-message");
                            errorContainer.textContent = '';
                        }
                    } catch (error) {
                        console.error(error);
                    }
                }
            }
        }

        // --> Validate Team Name
        const team = document.getElementById("teams_name_custom");
        if (team && team.value.trim() != '') {
            if (team.value !== originalTeamName){
                try {
                    const isAvailable = await check_name_availability('team', team.value);
                    if (!isAvailable) {
                        team.classList.add("is-invalid");
                        const errorContainer = document.getElementById("teams_name-validation-message");
                        errorContainer.textContent = "Team name is already taken";
                        validationMessages.push("Team name is already taken");
                    } else {
                        team.classList.remove('is-invalid');
                        const errorContainer = document.getElementById("username-validation-message");
                        errorContainer.textContent = '';
                    }
                } catch (error) {
                    console.error(error);
                }
            }
        }

        // --> Validate Role Name
        const role = document.getElementById("role_name_custom");
        if (role && role.value.trim() != '') {
            if (role.value !== originalRoleName){
                try {
                    const isAvailable = await check_name_availability('role', role.value);
                    if (!isAvailable) {
                        role.classList.add("is-invalid");
                        const errorContainer = document.getElementById("role_name-validation-message");
                        errorContainer.textContent = "Role name is already taken";
                        validationMessages.push("Role name is already taken");
                    } else {
                        team.classList.remove('is-invalid');
                        const errorContainer = document.getElementById("role_name-validation-message");
                        errorContainer.textContent = '';
                    }
                } catch (error) {
                    console.error(error);
                }
            }
        }


        // Verfiy Validations and submit 
        if (validationMessages.length === 0) {this.form.submit();}
    }


    // ------------------ Needed Functions ------------------
    handleValidationFailure(element, errorMessageBoxId, errorMessage) {
        element.classList.add('is-invalid');
        const errorContainer = document.getElementById(errorMessageBoxId);
        errorContainer.textContent = errorMessage;
    }        

    handleValidationSuccess(element, errorMessageBoxId) {
        element.classList.remove('is-invalid');
        const errorContainer = document.getElementById(errorMessageBoxId);
        errorContainer.textContent = '';
    }

    validatePassword(password) {
        const passwordRegex = /^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*()_+|~\-=`{}[\]:";'<>,./])\S{8,}$/;
        if (!passwordRegex.test(password)) {
            let errorMessage = "Password must include:\n";

            if (!/(?=.*\d)/.test(password)) {
                errorMessage += "- at least one number\n";
            }

            if (!/(?=.*[a-z])/.test(password)) {
                errorMessage += "- at least one lowercase letter\n";
            }

            if (!/(?=.*[A-Z])/.test(password)) {
                errorMessage += "- at least one uppercase letter\n";
            }

            if (!/(?=.*[!@#$%^&*()_+|~\-=`{}[\]:";'<>,./])/.test(password)) {
                errorMessage += "- at least one symbol\n";
            }

            if (password.length < 8) {
                errorMessage += "- be at least 8 characters long\n";
            }

            return errorMessage;
        }
        return '';
    }

}

// Send an AJAX GET request function
async function check_name_availability(model, name) {
    return new Promise(function(resolve, reject) {
        $.ajax({
            type: "GET",
            url: '/users/check_name_availability',
            data: { model:model, name:name},
            dataType: "json",
            success: function(response) {
                if (response.status === "success") {
                    // Username is available
                    resolve(true);
                } else {
                    // Username already exists
                    resolve(false);
                }
            },
            error: function() {
                reject("Error occurred");
            }
        });
    });
}

// Get The form in the page with the id  validateForm and initiate the class
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('validateForm'); const form2 = document.getElementById('validateForm2');
    if (form) {new FormValidator(form);}
    if (form2) {new FormValidator(form2);}
});