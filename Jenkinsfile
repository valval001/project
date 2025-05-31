pipeline {
    agent any

    tools {
        dependencyCheck 'OWASP'  // This should match your tool name
    }

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

        stage('Bandit Security Scan') {
            steps {
                sh '''
                    echo "Running Bandit security scan..."
                    export PATH=$PATH:/var/lib/jenkins/.local/bin
                    bandit -r . -f html -o bandit-report.html || true
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'bandit-report.html', fingerprint: true
                }
            }
        }

        stage('OWASP Dependency-Check') {
            steps {
                // Run dependency-check scan on the workspace directory
                dependencyCheck additionalArguments: '', odcInstallation: 'OWASP', pattern: '**/requirements.txt', skipOnError: false, failBuildOnCVSS: 7.0
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

        stage('Trivy Dockerfile Scan') {
            steps {
                sh '''
                    echo "Scanning Dockerfile for misconfigurations..."
                    trivy config Dockerfile > trivy-dockerfile-report.txt || true
                    cat trivy-dockerfile-report.txt
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    sh "docker build -t ${IMAGE_NAME} ."
                }
            }
        }

        stage('Trivy Image Scan') {
            steps {
                sh '''
                    echo "Scanning Docker image for vulnerabilities..."
                    export TRIVY_DISABLE_VEX_NOTICE=true
                    trivy image --ignore-unfixed --exit-code 1 --severity CRITICAL ${IMAGE_NAME} > trivy-image-report.txt || true
                    cat trivy-image-report.txt

                    # Fail if critical vulnerabilities are found
                    if grep -q "CRITICAL" trivy-image-report.txt; then
                        echo "Critical vulnerabilities found in Docker image."
                        echo "Removing the Image....."
                        docker rmi ${IMAGE_NAME}
                        echo "Image Removed....."
                        exit 1
                    fi
                '''
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

    post {
        always {
            dependencyCheckPublisher pattern: '**/dependency-check-report.xml'
        }
    }
   
}
