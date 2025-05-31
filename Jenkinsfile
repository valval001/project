pipeline {
    agent any

    environment {
        SONARQUBE = 'MySonarQube'
        SONAR_TOKEN = credentials('sonar-token')
        FLASK_SECRET_KEY = credentials('flask-secret')
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-credentials')
        IMAGE_NAME = 'ditisspriyanshu/jenkins:latest'
        DEPENDENCY_CHECK_HOME = tool 'OWASP'
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
                    bandit -r . -f html -o bandit-report.html -f sarif -o bandit-report.sarif || true
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'bandit-report.*', fingerprint: true
                    recordIssues enabledForFailure: true, tools: [sarif(pattern: 'bandit-report.sarif')]
                    publishHTML(target: [
                        reportName: 'Bandit Report',
                        reportDir: '.',
                        reportFiles: 'bandit-report.html',
                        keepAll: true
                    ])
                }
            }
        }

        stage('OWASP Dependency Check') {
            steps {
                sh '''
                    echo "Running OWASP Dependency Check..."
                    mkdir -p dependency-check-report
                    $DEPENDENCY_CHECK_HOME/bin/dependency-check.sh \
                    --project "MyProject" \
                    --scan . \
                    --format ALL \
                    --out dependency-check-report
                '''
            }
            post {
                always {
                    dependencyCheckPublisher(
                        failedTotalCritical: 0,
                        unstableTotalHigh: 5,
                        unstableTotalMedium: 10,
                        failedNewCritical: 0,
                        unstableNewHigh: 5,
                        unstableNewMedium: 10
                    )
                    archiveArtifacts artifacts: 'dependency-check-report/dependency-check-report.*', fingerprint: true
                }
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
                    trivy config --format table --output trivy-dockerfile-report.html Dockerfile || true
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'trivy-dockerfile-report.html', fingerprint: true
                    publishHTML(target: [
                        reportName: 'Trivy Dockerfile Report',
                        reportDir: '.',
                        reportFiles: 'trivy-dockerfile-report.html',
                        keepAll: true
                    ])
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

        stage('Trivy Image Scan') {
            steps {
                sh '''
                    echo "Scanning Docker image for vulnerabilities..."
                    export TRIVY_DISABLE_VEX_NOTICE=true
                    trivy image --format json --output trivy-image-report.json ${IMAGE_NAME} || true
                    trivy image --format table --output trivy-image-report.html ${IMAGE_NAME} || true

                    cat trivy-image-report.html

                    if grep -q "CRITICAL" trivy-image-report.html; then
                        echo "Critical vulnerabilities found in Docker image."
                        docker rmi ${IMAGE_NAME}
                        exit 1
                    fi
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'trivy-image-report.*', fingerprint: true
                    recordIssues enabledForFailure: true, tools: [trivy(pattern: 'trivy-image-report.json')]
                    publishHTML(target: [
                        reportName: 'Trivy Image Report',
                        reportDir: '.',
                        reportFiles: 'trivy-image-report.html',
                        keepAll: true
                    ])
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

    post {
        always {
            cleanWs()
        }
    }
}
