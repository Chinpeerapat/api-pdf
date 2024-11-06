from flask import Flask

app = Flask(__name__)
api = Api(app, version='1.0', title='PDF Analyzer API',
          description='API for analyzing PDF documents using Anthropic\'s Claude model')

# Add a basic root route
@app.route('/')
def home():
    return jsonify({"message": "Welcome to the PDF Analyzer API", "swagger_ui": "/swagger"})


# Set your Anthropic API key as an environment variable
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

# Default prompt for general usage
DEFAULT_PROMPT = "Please analyze this PDF and provide a summary of its contents, including key points and main topics covered."

# Define the namespace
ns = api.namespace('pdf', description='PDF operations')

# Define the input model
pdf_input = api.model('PDFInput', {
    'file': fields.Raw(description='PDF file to analyze', required=True),
    'prompt': fields.String(description='Custom prompt for analysis', required=False)
})

# Define the output model
pdf_output = api.model('PDFOutput', {
    'analysis': fields.String(description='Analysis result from Claude')
})

@ns.route('/analyze')
class PDFAnalyzer(Resource):
    @api.expect(pdf_input)
    @api.marshal_with(pdf_output, code=200, description='Successful analysis')
    @api.response(400, 'Validation Error')
    @api.response(500, 'Internal Server Error')
    def post(self):
        """Analyze a PDF file using Anthropic's Claude model"""
        if 'file' not in request.files:
            api.abort(400, "No file part")
        
        file = request.files['file']
        if file.filename == '':
            api.abort(400, "No selected file")
        
        if file and file.filename.lower().endswith('.pdf'):
            # Read the PDF file
            pdf_content = file.read()
            pdf_data = base64.standard_b64encode(pdf_content).decode("utf-8")
            
            # Get the prompt from the request, or use the default prompt
            prompt = request.form.get('prompt', DEFAULT_PROMPT)
            
            # Create Anthropic client
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            
            try:
                # Send API request to Anthropic
                message = client.beta.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    betas=["pdfs-2024-09-25"],
                    max_tokens=8192,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "document",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "application/pdf",
                                        "data": pdf_data
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ],
                )
                
                return {'analysis': message.content[0].text}
            
            except Exception as e:
                api.abort(500, f"An error occurred: {str(e)}")
        
        api.abort(400, "Invalid file format. Please upload a PDF file.")

if __name__ == "__main__":
    app.run()
