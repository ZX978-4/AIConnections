#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ModelKin demo script.
Run this after the API server is up to validate key endpoints.
"""

import json
import time
from pathlib import Path

import requests


class ModelKinDemo:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url

    def test_health(self):
        """Test API health."""
        print("Testing API health...")
        try:
            response = requests.get(f"{self.base_url}/api/health")
            if response.status_code == 200:
                data = response.json()
                print("API is running.")
                print(f"  Nodes: {data['nodes']}")
                print(f"  Edges: {data['edges']}")
                return True
            print(f"Unexpected status: {response.status_code}")
            return False
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def test_model_search(self, query="llama"):
        """Test model search."""
        print(f"\nTesting model search: '{query}'")
        try:
            response = requests.get(f"{self.base_url}/api/models?q={query}")
            if response.status_code == 200:
                models = response.json()
                print(f"Found {len(models)} matches")
                for i, model in enumerate(models[:5]):
                    print(f"  {i + 1}. {model}")
                return models
            print(f"Search failed: {response.status_code}")
            return []
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def test_lineage_visualization(self, model_id):
        """Test lineage retrieval."""
        print(f"\nTesting lineage: {model_id}")
        try:
            response = requests.get(f"{self.base_url}/api/model/{model_id}/lineage?depth=2")
            if response.status_code == 200:
                data = response.json()
                print("Lineage fetched successfully.")
                print(f"  Center model: {data['model']['id']}")
                print(f"  Ancestors: {data['stats']['ancestors_count']}")
                print(f"  Descendants: {data['stats']['descendants_count']}")
                print(f"  Total relations: {data['stats']['total_related']}")
                return data
            print(f"Fetch failed: {response.status_code}")
            return None
        except Exception as e:
            print(f"Lineage error: {e}")
            return None

    def test_sbom_export(self, model_id):
        """Test SBOM export."""
        print(f"\nTesting SBOM export: {model_id}")
        try:
            response = requests.get(f"{self.base_url}/api/model/{model_id}/sbom", timeout=10)
            if response.status_code == 200:
                sbom = response.json()
                print("SBOM generated.")
                print(f"  SPDX Version: {sbom['spdxVersion']}")
                print(f"  Document ID: {sbom['SPDXID']}")
                print(f"  Packages: {len(sbom['packages'])}")
                print(f"  Relationships: {len(sbom['relationships'])}")

                filename = f"sbom-{model_id.replace('/', '-')}.json"
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(sbom, f, indent=2, ensure_ascii=False)
                print(f"  Saved to: {filename}")
                return sbom
            print(f"SBOM failed: {response.status_code}")
            print(f"  Error: {response.text[:200]}...")
            return None
        except Exception as e:
            print(f"SBOM error: {e}")
            return None

    def test_integrity_verification(self, model_id):
        """Test integrity verification."""
        print(f"\nTesting integrity verification: {model_id}")
        try:
            response = requests.get(f"{self.base_url}/api/model/{model_id}/verify")
            if response.status_code == 200:
                verification = response.json()
                print("Verification completed.")
                print(f"  Model ID: {verification['model_id']}")
                print(f"  Hash: {verification['model_hash'][:16]}...")
                print(f"  Status: {verification['verification_status']}")
                print(f"  Lineage OK: {verification['lineage_integrity']}")
                print(f"  Timestamp: {verification['timestamp']}")
                return verification
            print(f"Verification failed: {response.status_code}")
            return None
        except Exception as e:
            print(f"Verification error: {e}")
            return None

    def run_full_demo(self):
        """Run end-to-end demo."""
        print("Running ModelKin demo")
        print("=" * 50)

        if not self.test_health():
            print("API not ready. Start it with: python app.py")
            return

        models = self.test_model_search("llama")
        if not models:
            return

        test_model = models[0]
        print(f"\nSelected model: {test_model}")

        lineage_data = self.test_lineage_visualization(test_model)
        if not lineage_data:
            return

        sbom_data = self.test_sbom_export(test_model)
        if not sbom_data:
            return

        verification_data = self.test_integrity_verification(test_model)
        if not verification_data:
            return

        print("\n" + "=" * 50)
        print("Demo completed successfully.")
        print(f"Open: {self.base_url}")


def main():
    demo = ModelKinDemo()
    demo.run_full_demo()


if __name__ == "__main__":
    main()
