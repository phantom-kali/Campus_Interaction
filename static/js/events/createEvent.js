document.addEventListener('DOMContentLoaded', function() {
    // Initialize variables
    let currentStep = 1;
    const totalSteps = 3;
    const form = document.getElementById('event-form');
    const progressBar = document.querySelector('.progress-bar');
    const steps = document.querySelectorAll('.form-step');
    const nextButtons = document.querySelectorAll('.next-step');
    const prevButtons = document.querySelectorAll('.prev-step');
    const stepIndicators = document.querySelectorAll('.step');
    const stepConnectors = document.querySelectorAll('.step-connector');

    // Function to validate current step
    function validateStep(stepNumber) {
        const currentStepElement = document.querySelector(`#step${stepNumber}`);
        let isValid = true;
        
        const requiredFields = currentStepElement.querySelectorAll('input[required], select[required], textarea[required]');
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                field.classList.add('is-invalid');
                // Add invalid feedback if not exists
                if (!field.nextElementSibling?.classList.contains('invalid-feedback')) {
                    const feedback = document.createElement('div');
                    feedback.className = 'invalid-feedback';
                    feedback.textContent = 'This field is required';
                    field.parentNode.appendChild(feedback);
                }
            } else {
                field.classList.remove('is-invalid');
            }
        });

        return isValid;
    }

    // Function to show step
    function showStep(stepNumber) {
        steps.forEach(step => step.classList.remove('active'));
        document.querySelector(`#step${stepNumber}`).classList.add('active');
        
        // Update progress bar
        const progress = ((stepNumber - 1) / (totalSteps - 1)) * 100;
        progressBar.style.width = `${progress}%`;
        
        // Update step indicators
        stepIndicators.forEach((indicator, index) => {
            indicator.classList.remove('active', 'completed');
            if (index + 1 === stepNumber) {
                indicator.classList.add('active');
            } else if (index + 1 < stepNumber) {
                indicator.classList.add('completed');
            }
        });

        // Update connectors
        stepConnectors.forEach((connector, index) => {
            connector.classList.toggle('active', index < stepNumber - 1);
        });

        currentStep = stepNumber;
    }

    // Next button click handler
    nextButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            if (validateStep(currentStep) && currentStep < totalSteps) {
                showStep(currentStep + 1);
            }
        });
    });

    // Previous button click handler
    prevButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            if (currentStep > 1) {
                showStep(currentStep - 1);
            }
        });
    });

    // Handle form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        if (validateStep(currentStep)) {
            // Submit the form if all validations pass
            this.submit();
        }
    });

    // Character counter for description
    const descriptionField = document.getElementById('id_description');
    const charCount = document.getElementById('char-count');
    
    if (descriptionField && charCount) {
        descriptionField.addEventListener('input', () => {
            const count = descriptionField.value.length;
            charCount.textContent = count;
            if (count > 500) {
                descriptionField.value = descriptionField.value.substring(0, 500);
                charCount.textContent = 500;
            }
        });
    }

    // Event type toggle
    const eventType = document.getElementById('id_event_type');
    const physicalFields = document.getElementById('physical-fields');
    const textFields = document.getElementById('text-fields');

    if (eventType && physicalFields && textFields) {
        function toggleEventType() {
            if (eventType.value === 'physical') {
                physicalFields.style.display = 'block';
                textFields.style.display = 'none';
            } else {
                physicalFields.style.display = 'none';
                textFields.style.display = 'block';
            }
        }

        eventType.addEventListener('change', toggleEventType);
        toggleEventType(); // Initial toggle
    }

    // Date validation
    const startDateInput = document.getElementById('id_start_date');
    const endDateInput = document.getElementById('id_end_date');

    if (startDateInput && endDateInput) {
        function setMinDates() {
            const now = new Date();
            now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
            startDateInput.min = now.toISOString().slice(0, 16);
            if (startDateInput.value) {
                endDateInput.min = startDateInput.value;
            }
        }

        startDateInput.addEventListener('input', function() {
            endDateInput.min = this.value;
            if (endDateInput.value && endDateInput.value < this.value) {
                endDateInput.value = this.value;
            }
        });

        setMinDates();
    }

    // Image handling
    const dropZone = document.getElementById('drop-zone');
    const imageInput = document.getElementById('id_image');
    
    if (dropZone && imageInput) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('border-primary');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('border-primary');
            });
        });

        dropZone.addEventListener('drop', handleDrop);
        dropZone.addEventListener('click', () => imageInput.click());
        imageInput.addEventListener('change', () => handleFiles(imageInput.files));

        function handleDrop(e) {
            const files = e.dataTransfer.files;
            handleFiles(files);
        }

        function handleFiles(files) {
            if (files.length > 0) {
                const file = files[0];
                if (file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        document.getElementById('image-preview').innerHTML = 
                            `<img src="${e.target.result}" class="preview-image" alt="Preview">`;
                    };
                    reader.readAsDataURL(file);
                } else {
                    alert('Please upload a valid image file.');
                }
            }
        }
    }

    // Initialize the first step
    showStep(1);
});