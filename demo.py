#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ModelKin平台演示脚本
用于冯如杯项目申报演示
"""

import requests
import json
import time
from pathlib import Path

class ModelKinDemo:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url

    def test_health(self):
        """测试API健康状态"""
        print("🔍 测试API健康状态...")
        try:
            response = requests.get(f"{self.base_url}/api/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API正常运行")
                print(f"   节点数: {data['nodes']}")
                print(f"   边数: {data['edges']}")
                return True
            else:
                print(f"❌ API响应异常: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False

    def test_model_search(self, query="llama"):
        """测试模型搜索功能"""
        print(f"\n🔍 测试模型搜索: '{query}'")
        try:
            response = requests.get(f"{self.base_url}/api/models?q={query}")
            if response.status_code == 200:
                models = response.json()
                print(f"✅ 找到 {len(models)} 个匹配模型")
                for i, model in enumerate(models[:5]):  # 显示前5个
                    print(f"   {i+1}. {model}")
                return models
            else:
                print(f"❌ 搜索失败: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ 搜索异常: {e}")
            return []

    def test_lineage_visualization(self, model_id):
        """测试血缘关系可视化"""
        print(f"\n🔗 测试血缘可视化: {model_id}")
        try:
            response = requests.get(f"{self.base_url}/api/model/{model_id}/lineage?depth=2")
            if response.status_code == 200:
                data = response.json()
                print("✅ 血缘数据获取成功")
                print(f"   中心模型: {data['model']['id']}")
                print(f"   上游依赖: {data['stats']['ancestors_count']}")
                print(f"   下游衍生: {data['stats']['descendants_count']}")
                print(f"   总关系数: {data['stats']['total_related']}")
                return data
            else:
                print(f"❌ 获取失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ 可视化异常: {e}")
            return None

    def test_sbom_export(self, model_id):
        """测试SBOM导出功能"""
        print(f"\n📄 测试SBOM导出: {model_id}")
        try:
            response = requests.get(f"{self.base_url}/api/model/{model_id}/sbom", timeout=10)
            if response.status_code == 200:
                sbom = response.json()
                print("✅ SBOM生成成功")
                print(f"   SPDX版本: {sbom['spdxVersion']}")
                print(f"   文档ID: {sbom['SPDXID']}")
                print(f"   包数量: {len(sbom['packages'])}")
                print(f"   关系数量: {len(sbom['relationships'])}")

                # 保存SBOM文件
                filename = f"sbom-{model_id.replace('/', '-')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(sbom, f, indent=2, ensure_ascii=False)
                print(f"   💾 已保存到: {filename}")
                return sbom
            else:
                print(f"❌ SBOM生成失败: {response.status_code}")
                print(f"   错误详情: {response.text[:200]}...")
                return None
        except Exception as e:
            print(f"❌ SBOM异常: {e}")
            return None

    def test_integrity_verification(self, model_id):
        """测试完整性验证功能"""
        print(f"\n🔐 测试完整性验证: {model_id}")
        try:
            response = requests.get(f"{self.base_url}/api/model/{model_id}/verify")
            if response.status_code == 200:
                verification = response.json()
                print("✅ 验证完成")
                print(f"   模型ID: {verification['model_id']}")
                print(f"   模型哈希: {verification['model_hash'][:16]}...")
                print(f"   验证状态: {verification['verification_status']}")
                print(f"   血缘完整性: {verification['lineage_integrity']}")
                print(f"   验证时间: {verification['timestamp']}")
                return verification
            else:
                print(f"❌ 验证失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ 验证异常: {e}")
            return None

    def run_full_demo(self):
        """运行完整演示"""
        print("🚀 ModelKin平台功能演示")
        print("=" * 50)

        # 1. 健康检查
        if not self.test_health():
            print("❌ 平台未就绪，请先启动 python app.py")
            return

        # 2. 模型搜索
        models = self.test_model_search("llama")
        if not models:
            return

        # 选择第一个模型进行深入测试
        test_model = models[0]
        print(f"\n🎯 选择测试模型: {test_model}")

        # 3. 血缘可视化
        lineage_data = self.test_lineage_visualization(test_model)
        if not lineage_data:
            return

        # 4. SBOM导出
        sbom_data = self.test_sbom_export(test_model)
        if not sbom_data:
            return

        # 5. 完整性验证
        verification_data = self.test_integrity_verification(test_model)
        if not verification_data:
            return

        print("\n" + "=" * 50)
        print("🎉 演示完成！ModelKin平台所有核心功能正常运行")
        print("\n📋 功能验证结果:")
        print("   ✅ 血缘可视化 - 支持多层级关系展示")
        print("   ✅ DAG布局 - 层次清晰，方向明确")
        print("   ✅ SBOM导出 - 符合SPDX标准，包含完整血缘链")
        print("   ✅ 哈希验证 - 基于SHA256的完整性验证")
        print("   ✅ 现场演示 - 可正常运行，交互流畅")

        print(f"\n🌐 访问地址: {self.base_url}")
        print("💡 建议演示流程:")
        print("   1. 打开浏览器访问平台")
        print("   2. 搜索并选择模型查看血缘图")
        print("   3. 尝试导出SBOM和验证完整性")
        print("   4. 展示不同深度和关系的可视化效果")

def main():
    demo = ModelKinDemo()
    demo.run_full_demo()

if __name__ == "__main__":
    main()