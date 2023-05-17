from flask import Flask, request, render_template, jsonify
import json
import os
import boto3

app = Flask(__name__, template_folder='.')

# Create an SQS client
sqs = boto3.client('sqs', region_name='eu-north-1')


@app.route("/")
def home():
    return render_template('upload_form.html')


@app.route('/handle_information', methods=['POST'])
def handle_information():
    bug = request.form.get('bug')
    priority = request.form.get('priority')
    additional_info = request.form.get('additional_info')

    # Validate form data
    bug_form = {
        'bug': bug,
        'priority': priority,
        'additional_info': additional_info
    }

    # Map priority values to queue names
    queue_names = {
        'high_priority': 'High',
        'medium_priority': 'MediumLow',
        'low_priority': 'MediumLow'
    }

    # Call sendtoqueues function to send bug information to appropriate queue
    return sendtoqueues(priority, queue_names, sqs, bug_form)


@app.route('/createQueues', methods=['GET'])
def create_queues():
    # Create the High priority queue
    sqs.create_queue(QueueName='High')
    # Create the Medium/Low priority queue
    sqs.create_queue(QueueName='MediumLow')
    # Create the Dead Letter Queue (DLQ)
    sqs.create_queue(QueueName='DLQ')

    return jsonify({'message': 'Queues created successfully'}),


def sendtoqueues(priority, queue_names, sqs, bug_form):
    # Get the queue name based on priority, or default to DLQ
    queue_name = queue_names.get(priority, 'DLQ')
    try:
        # Construct the queue URL
        qURl = sqs.get_queue_url(QueueName=queue_name)['QueueUrl']
        # Send message to the queue with a 10-second delay
        response = sqs.send_message(
            QueueUrl=qURl,
            DelaySeconds=10,
            MessageBody=json.dumps(bug_form)
        )

        return jsonify(
            'Bug information submitted successfully')

    except Exception as e:
        return jsonify({'error': 'Failed to submit bug information to the queue'})


if __name__ == '__main__':
    app.run(debug=True)
