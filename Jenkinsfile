pipeline {
    agent any

    environment {
        SONARQUBE = 'MySonarQube'
        SONAR_TOKEN = credentials('sonar-token')
        FLASK_SECRET_KEY = credentials('flask-secret')
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-credentials')
        IMAGE_NAME = 'ditisspriyanshu/jenkins:latest'
    }

    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/valval001/project.git', branch: 'master'
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
                script {
                    sh "docker build -t ${IMAGE_NAME} ."
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    sh """
                        echo "${DOCKERHUB_CREDENTIALS_PSW}" | docker login -u "${DOCKERHUB_CREDENTIALS_USR}" --password-stdin
                        docker push ${IMAGE_NAME}
			docker logout
			docker rmi ${IMAGE_NAME}
                    """
                }
            }
        }
    }
}
