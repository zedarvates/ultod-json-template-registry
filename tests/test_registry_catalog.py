import unittest

from scripts.registry_catalog import build_catalog_index, validate_reference_graph


def entry(ref, file):
    template_id, version = ref.split("@", 1)
    family, slug = template_id.split(":", 1)
    return {
        "id": template_id,
        "family": family,
        "slug": slug,
        "version": version,
        "file": file,
        "validation_profile": "strict-v1",
    }


class CatalogIndexTests(unittest.TestCase):
    def test_duplicate_exact_reference_is_rejected(self):
        duplicate = entry(
            "items:iron-ore@1.0.0",
            "templates/items/iron-ore/v1.0.0/template.json",
        )
        index, errors = build_catalog_index(
            {"entries": [duplicate, dict(duplicate)], "aliases": []}
        )
        self.assertIsNone(index)
        self.assertEqual(
            errors,
            [
                "duplicate catalog file: templates/items/iron-ore/v1.0.0/template.json",
                "duplicate catalog reference: items:iron-ore@1.0.0",
            ],
        )

    def test_missing_dependency_is_rejected(self):
        source = entry(
            "recipes:iron-ingot@1.0.0",
            "templates/recipes/iron-ingot/v1.0.0/template.json",
        )
        index, errors = build_catalog_index({"entries": [source], "aliases": []})
        self.assertEqual(errors, [])
        documents = {
            "recipes:iron-ingot@1.0.0": {
                "dependencies": ["items:iron-ore@1.0.0"]
            }
        }
        self.assertEqual(
            validate_reference_graph(index, documents),
            [
                "recipes:iron-ingot@1.0.0: missing dependency "
                "items:iron-ore@1.0.0"
            ],
        )

    def test_alias_cycle_is_rejected(self):
        catalog = {
            "entries": [
                entry("items:a@1.0.0", "templates/items/a/v1.0.0/template.json"),
                entry("items:b@1.0.0", "templates/items/b/v1.0.0/template.json"),
            ],
            "aliases": [
                {"from": "items:a@1.0.0", "to": "items:b@1.0.0"},
                {"from": "items:b@1.0.0", "to": "items:a@1.0.0"},
            ],
        }
        index, errors = build_catalog_index(catalog)
        self.assertIsNone(index)
        self.assertEqual(
            errors,
            ["alias cycle: items:a@1.0.0 -> items:b@1.0.0 -> items:a@1.0.0"],
        )

    def test_supersession_must_resolve_and_cannot_target_self(self):
        source = entry(
            "items:iron-ore@1.0.0",
            "templates/items/iron-ore/v1.0.0/template.json",
        )
        source["supersedes"] = ["items:missing@0.1.0", "items:iron-ore@1.0.0"]
        index, errors = build_catalog_index({"entries": [source], "aliases": []})
        self.assertEqual(errors, [])
        self.assertEqual(
            validate_reference_graph(index, {"items:iron-ore@1.0.0": {}}),
            [
                "items:iron-ore@1.0.0: cannot supersede itself",
                "items:iron-ore@1.0.0: missing superseded reference items:missing@0.1.0",
            ],
        )


if __name__ == "__main__":
    unittest.main()
