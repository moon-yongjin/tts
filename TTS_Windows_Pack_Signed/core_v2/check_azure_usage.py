import os
import json
from azure.identity import DefaultAzureCredential, ServicePrincipalCredential
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient

def check_azure_usage():
    # 1. 서비스 계정 파일 로드 (core_v2/service_account.json)
    creds_path = os.path.join("core_v2", "service_account.json")
    if not os.path.exists(creds_path):
        print(f"❌ 서비스 계정 파일을 찾을 수 없습니다: {creds_path}")
        return

    with open(creds_path, "r", encoding="utf-8") as f:
        creds_data = json.load(f)

    # 2. 인증 설정 (Service Principal)
    try:
        credential = ServicePrincipalCredential(
            tenant_id=creds_data.get("project_id"), # 프로젝트 ID가 테넌트 ID와 다를 수 있으나 일단 시도
            client_id=creds_data.get("client_id"),
            client_secret="YOUR_CLIENT_SECRET" # JSON에 시크릿이 없으면 private_key를 써야 할 수도 있음
        )
        # Note: Google Service Account와 Azure Service Principal은 체계가 다릅니다.
        # 사용자님께서 주신 .json은 Google용인 것 같습니다. 
        # Azure용은 보통 'Subscription ID'와 'Tenant ID'가 필요합니다.
        
        print("⚠️ 주의: 제공된 .json 파일은 Google 서비스 계정 형식입니다.")
        print("Azure 조회를 위해 Azure 구독 ID(Subscription ID)가 필요합니다.")
        
        # 일단 환경 변수나 기존 설정에서 구독 정보를 찾아봅니다.
    except Exception as e:
        print(f"❌ 인증 설정 실패: {e}")

if __name__ == "__main__":
    print("🔍 Azure Usage Checker 가동...")
    # 실제로는 Azure CLI 로그인이 되어 있다면 아래 방식이 가장 정확합니다.
    try:
        from azure.identity import AzureCliCredential
        credential = AzureCliCredential()
        # 구독 ID는 수동 입력이 필요할 수 있음
        subscription_id = "b46dc11f-6fd4-43f3-a5bd-07761ddd59a9" 
        
        client = CognitiveServicesManagementClient(credential, subscription_id)
        
        # 모든 리전의 사용량 조회
        print("📊 Azure Cognitive Services 사용량 조회 중...")
        # (구체적인 리소스 그룹과 리소스 이름이 필요함)
    except ImportError:
        print("❌ azure-mgmt-cognitiveservices 라이브러리가 설치되지 않았습니다.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
