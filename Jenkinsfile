pipeline {
    agent any

    environment {
        SONARQUBE = 'MySonarQube'
        SONAR_TOKEN = credentials('sonar-token')
        FLASK_SECRET_KEY = credentials('flask-secret')
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-credentials')
        IMAGE_NAME = 'ditisspriyanshu/jenkins'

    }

    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/valval001/project.git', branch: 'master'
            }
        }
        stage('Set Up Virtual Environment') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Run Pytest') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest
                '''
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv(SONARQUBE) {
                    sh """
                        echo $FLASK_SECRET_KEY > /dev/null
                        sonar-scanner -Dsonar.login=${SONAR_TOKEN}
                    """
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build -t ${IMAGE_NAME}:latest -t .
                '''
            }
        }

        stage('Push Docker Image') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh """
                        echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                        docker push ${IMAGE_NAME}:latest
                        docker logout
                    """
                }
            }
        }
        stage('Remove Local Docker Image') {
            steps {
                sh 'docker rmi ${IMAGE_NAME}:latest'
            }
        }
    }

    post {
        always {
            echo 'Cleaning up virtual environment...'
            sh 'rm -rf venv'
        }
    }
}
