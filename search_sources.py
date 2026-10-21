# -*- coding: utf-8 -*-
"""
search_sources.py
Fonctions de recherche pour chaque source publique intégrée.
Toutes les fonctions retournent une liste de dictionnaires avec les clés :
title, url, snippet, meta, image (optionnel).
"""
import urllib.parse
import xml.etree.ElementTree as ET
from utils import http_get, truncate_text, clean_html


SOURCES = {
    "Google Scholar": {"category": "Academic", "icon": "🎓", "url": "https://scholar.google.com/scholar?q={q}", "api": False, "description": "Recherche académique Google Scholar"},
    "Semantic Scholar": {"category": "Academic", "icon": "📚", "url": "https://www.semanticscholar.org/search?q={q}", "api": True, "description": "Moteur de recherche sémantique académique"},
    "PubMed": {"category": "Academic", "icon": "🧬", "url": "https://pubmed.ncbi.nlm.nih.gov/?term={q}", "api": True, "description": "Base biomédicale PubMed"},
    "arXiv": {"category": "Academic", "icon": "⚛️", "url": "https://arxiv.org/search/?query={q}", "api": True, "description": "Prépublications scientifiques arXiv"},
    "CORE": {"category": "Academic", "icon": "🔬", "url": "https://core.ac.uk/search?q={q}", "api": False, "description": "Accès ouvert aux articles de recherche"},
    "BASE": {"category": "Academic", "icon": "📖", "url": "https://www.base-search.net/Search/Results?lookfor={q}", "api": False, "description": "Moteur de recherche académique Bielefeld"},
    "OpenAlex": {"category": "Academic", "icon": "🌐", "url": "https://openalex.org/works?page=1&filter=default.search%3A{q}", "api": True, "description": "Graph ouvert de la recherche mondiale"},
    "Crossref": {"category": "Academic", "icon": "🔗", "url": "https://search.crossref.org/?q={q}", "api": True, "description": "DOI et métadonnées de publications"},
    "DOAJ": {"category": "Academic", "icon": "📰", "url": "https://doaj.org/search/articles?source=%7B%22query%22%3A%7B%22query_string%22%3A%7B%22query%22%3A%22{q}%22%7D%7D%7D", "api": False, "description": "Directory of Open Access Journals"},
    "ERIC": {"category": "Academic", "icon": "🏫", "url": "https://eric.ed.gov/?q={q}", "api": False, "description": "Institute of Education Sciences"},
    "JSTOR": {"category": "Academic", "icon": "🏛️", "url": "https://www.jstor.org/action/doBasicSearch?Query={q}", "api": False, "description": "Archives académiques JSTOR"},
    "GitHub Code Search": {"category": "Code", "icon": "🐙", "url": "https://github.com/search?q={q}&type=code", "api": True, "description": "Recherche de code sur GitHub"},
    "Sourcegraph": {"category": "Code", "icon": "🔍", "url": "https://sourcegraph.com/search?q={q}", "api": False, "description": "Recherche universelle de code"},
    "grep.app": {"category": "Code", "icon": "🧩", "url": "https://grep.app/search?q={q}", "api": False, "description": "Recherche de code dans des dépôts publics"},
    "GitLab": {"category": "Code", "icon": "🦊", "url": "https://gitlab.com/search?search={q}", "api": False, "description": "Recherche de projets GitLab"},
    "Stack Overflow": {"category": "Code", "icon": "🥞", "url": "https://stackoverflow.com/search?q={q}", "api": True, "description": "Questions et réponses techniques"},
    "npm": {"category": "Code", "icon": "📦", "url": "https://www.npmjs.com/search?q={q}", "api": True, "description": "Registry de packages Node.js"},
    "PyPI": {"category": "Code", "icon": "🐍", "url": "https://pypi.org/search/?q={q}", "api": True, "description": "Python Package Index"},
    "crates.io": {"category": "Code", "icon": "🦀", "url": "https://crates.io/search?q={q}", "api": True, "description": "Registry Rust"},
    "Docker Hub": {"category": "Code", "icon": "🐳", "url": "https://hub.docker.com/search?q={q}", "api": True, "description": "Images Docker publiques"},
    "Hugging Face": {"category": "Code", "icon": "🤗", "url": "https://huggingface.co/search/full-text?q={q}", "api": True, "description": "Modèles et datasets IA"},
    "Google Images": {"category": "Images", "icon": "🖼️", "url": "https://www.google.com/search?tbm=isch&q={q}", "api": False, "description": "Recherche d'images Google"},
    "Bing Images": {"category": "Images", "icon": "🌅", "url": "https://www.bing.com/images/search?q={q}", "api": False, "description": "Recherche d'images Bing"},
    "Flickr": {"category": "Images", "icon": "📷", "url": "https://www.flickr.com/search/?text={q}", "api": True, "description": "Photos partagées Flickr"},
    "Unsplash": {"category": "Images", "icon": "🌄", "url": "https://unsplash.com/s/photos/{q}", "api": False, "description": "Photos libres de droits Unsplash"},
    "Pexels": {"category": "Images", "icon": "🎨", "url": "https://www.pexels.com/search/{q}/", "api": False, "description": "Banque d'images Pexels"},
    "YouTube": {"category": "Videos", "icon": "▶️", "url": "https://www.youtube.com/results?search_query={q}", "api": False, "description": "Recherche de vidéos YouTube"},
    "Vimeo": {"category": "Videos", "icon": "🎬", "url": "https://vimeo.com/search?q={q}", "api": False, "description": "Vidéos Vimeo"},
    "Dailymotion": {"category": "Videos", "icon": "📺", "url": "https://www.dailymotion.com/search/{q}", "api": False, "description": "Vidéos Dailymotion"},
    "Internet Archive": {"category": "Archives", "icon": "📼", "url": "https://archive.org/search?query={q}", "api": True, "description": "Archives numériques"},
    "Google Maps": {"category": "Maps", "icon": "🗺️", "url": "https://www.google.com/maps/search/{q}", "api": False, "description": "Cartes et lieux Google"},
    "OpenStreetMap": {"category": "Maps", "icon": "🌍", "url": "https://www.openstreetmap.org/search?query={q}", "api": True, "description": "Carte libre OpenStreetMap"},
    "Apple Maps": {"category": "Maps", "icon": "🍎", "url": "https://maps.apple.com/?q={q}", "api": False, "description": "Cartes Apple"},
    "Bing Maps": {"category": "Maps", "icon": "🧭", "url": "https://www.bing.com/maps?q={q}", "api": False, "description": "Cartes Bing"},
    "HERE WeGo": {"category": "Maps", "icon": "🛣️", "url": "https://wego.here.com/search/{q}", "api": False, "description": "Cartes et navigation HERE"},
    "MapQuest": {"category": "Maps", "icon": "🚩", "url": "https://www.mapquest.com/search/results?query={q}", "api": False, "description": "Cartes MapQuest"},
    "Yandex Maps": {"category": "Maps", "icon": "🇷🇺", "url": "https://yandex.com/maps/?text={q}", "api": False, "description": "Cartes Yandex"},
    "Baidu Maps": {"category": "Maps", "icon": "🇨🇳", "url": "https://map.baidu.com/search/{q}", "api": False, "description": "Cartes Baidu"},
}


SEARCH_FUNCTIONS = {
    "Semantic Scholar": search_semantic_scholar,
    "PubMed": search_pubmed,
    "arXiv": search_arxiv,
    "OpenAlex": search_openalex,
    "Crossref": search_crossref,
    "Stack Overflow": search_stackoverflow,
    "npm": search_npm,
    "PyPI": search_pypi,
    "crates.io": search_crates,
    "Docker Hub": search_dockerhub,
    "Hugging Face": search_huggingface,
    "Flickr": search_flickr,
    "Internet Archive": search_internet_archive,
    "OpenStreetMap": search_openstreetmap,
}


def build_web_result(source_name: str, query: str):
    """Construit un résultat de base pour les sources sans API."""
    meta = SOURCES[source_name]
    url = meta["url"].format(q=urllib.parse.quote(query))
    return {
        "title": f"Rechercher '{query}' sur {source_name}",
        "url": url,
        "snippet": meta["description"],
        "meta": "Lien web direct",
        "image": None,
    }




def search_semantic_scholar(query, limit=5):
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {"query": query, "fields": "title,authors,year,abstract,url", "limit": limit}
    data = http_get(url, params=params, timeout=20)
    results = []
    if isinstance(data, dict) and "data" in data:
        for item in data["data"]:
            authors = ", ".join([a.get("name", "") for a in item.get("authors", [])[:3]])
            results.append({
                "title": item.get("title", "Sans titre"),
                "url": item.get("url", ""),
                "snippet": truncate_text(item.get("abstract", "")),
                "meta": f"{item.get('year', 'N/A')} - {authors}",
                "image": None,
            })
    return results


def search_pubmed(query, limit=5):
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {"db": "pubmed", "term": query, "retmax": limit, "retmode": "json"}
    search_data = http_get(search_url, params=search_params, timeout=20)
    results = []
    if isinstance(search_data, dict) and "esearchresult" in search_data:
        ids = search_data["esearchresult"].get("idlist", [])
        if ids:
            summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
            summary_params = {"db": "pubmed", "id": ",".join(ids), "retmode": "json"}
            summary_data = http_get(summary_url, params=summary_params, timeout=20)
            if isinstance(summary_data, dict) and "result" in summary_data:
                for pmid in ids:
                    info = summary_data["result"].get(pmid, {})
                    results.append({
                        "title": info.get("title", "PubMed Article"),
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        "snippet": truncate_text(", ".join(info.get("authors", [])[:3])),
                        "meta": f"PMID:{pmid} - {info.get('source', '')} - {info.get('pubdate', '')}",
                        "image": None,
                    })
    return results


def search_arxiv(query, limit=5):
    url = "http://export.arxiv.org/api/query"
    params = {"search_query": f"all:{query}", "start": 0, "max_results": limit}
    data = http_get(url, params=params, timeout=20)
    results = []
    if isinstance(data, str):
        try:
            root = ET.fromstring(data)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", ns):
                title = entry.findtext("atom:title", default="", namespaces=ns).replace("\n", " ")
                link = entry.find("atom:link", ns)
                url_val = link.get("href") if link is not None else ""
                summary = entry.findtext("atom:summary", default="", namespaces=ns)
                authors = [a.findtext("atom:name", default="", namespaces=ns) for a in entry.findall("atom:author", ns)]
                results.append({
                    "title": title or "arXiv Paper",
                    "url": url_val,
                    "snippet": truncate_text(clean_html(summary)),
                    "meta": f"arXiv - {', '.join(authors[:3])}",
                    "image": None,
                })
        except Exception:
            pass
    return results


def search_openalex(query, limit=5):
    url = "https://api.openalex.org/works"
    params = {"filter": f"default.search:{query}", "per-page": limit, "select": "id,display_name,publication_year,authorships,abstract_inverted_index"}
    data = http_get(url, params=params, timeout=20)
    results = []
    if isinstance(data, dict) and "results" in data:
        for item in data["results"]:
            authors = ", ".join([a.get("author", {}).get("display_name", "") for a in item.get("authorships", [])[:3]])
            results.append({
                "title": item.get("display_name", "OpenAlex Work"),
                "url": item.get("id", ""),
                "snippet": "OpenAlex indexed work",
                "meta": f"{item.get('publication_year', 'N/A')} - {authors}",
                "image": None,
            })
    return results


def search_crossref(query, limit=5):
    url = "https://api.crossref.org/works"
    params = {"query": query, "rows": limit}
    data = http_get(url, params=params, timeout=20)
    results = []
    if isinstance(data, dict):
        items = data.get("message", {}).get("items", [])
        for item in items:
            authors = []
            for a in item.get("author", [])[:3]:
                authors.append(f"{a.get('given', '')} {a.get('family', '')}".strip())
            results.append({
                "title": item.get("title", ["Crossref Work"])[0],
                "url": item.get("URL", ""),
                "snippet": truncate_text(item.get("abstract", "")),
                "meta": f"{item.get('published-print', {}).get('date-parts', [['N/A']])[0][0]} - {', '.join(authors)}",
                "image": None,
            })
    return results


def search_stackoverflow(query, limit=5):
    url = "https://api.stackexchange.com/2.3/search/advanced"
    params = {"order": "desc", "sort": "relevance", "q": query, "site": "stackoverflow", "pagesize": limit}
    data = http_get(url, params=params, timeout=20)
    results = []
    if isinstance(data, dict) and "items" in data:
        for item in data["items"]:
            results.append({
                "title": item.get("title", "Question Stack Overflow"),
                "url": item.get("link", ""),
                "snippet": f"Score: {item.get('score', 0)} | Réponses: {item.get('answer_count', 0)}",
                "meta": f"Tags: {', '.join(item.get('tags', [])[:3])}",
                "image": None,
            })
    return results


def search_npm(query, limit=5):
    url = "https://registry.npmjs.org/-/v1/search"
    params = {"text": query, "size": limit}
    data = http_get(url, params=params, timeout=20)
    results = []
    if isinstance(data, dict) and "objects" in data:
        for obj in data["objects"]:
            pkg = obj.get("package", {})
            results.append({
                "title": pkg.get("name", "npm Package"),
                "url": pkg.get("links", {}).get("npm", f"https://www.npmjs.com/package/{pkg.get('name', '')}"),
                "snippet": truncate_text(pkg.get("description", "")),
                "meta": f"v{pkg.get('version', '')} - {pkg.get('publisher', {}).get('username', '')}",
                "image": None,
            })
    return results


def search_pypi(query, limit=5):
    url = f"https://pypi.org/pypi/{query}/json"
    data = http_get(url, timeout=20)
    results = []
    if isinstance(data, dict) and "info" in data:
        info = data["info"]
        results.append({
            "title": info.get("name", "PyPI Package"),
            "url": info.get("project_urls", {}).get("Homepage", info.get("package_url", "")),
            "snippet": truncate_text(info.get("summary", "")),
            "meta": f"v{info.get('version', '')} - {info.get('author', '')}",
            "image": None,
        })
    return results


def search_crates(query, limit=5):
    url = "https://crates.io/api/v1/crates"
    params = {"q": query, "per_page": limit}
    headers = {"User-Agent": "Mozilla/5.0"}
    data = http_get(url, params=params, headers=headers, timeout=20)
    results = []
    if isinstance(data, dict) and "crates" in data:
        for item in data["crates"]:
            results.append({
                "title": item.get("name", "crate"),
                "url": f"https://crates.io/crates/{item.get('name', '')}",
                "snippet": truncate_text(item.get("description", "")),
                "meta": f"v{item.get('newest_version', '')} - DL:{item.get('downloads', 0)}",
                "image": None,
            })
    return results


def search_dockerhub(query, limit=5):
    url = "https://hub.docker.com/api/search/v3/catalog/search"
    params = {"query": query, "page_size": limit}
    data = http_get(url, params=params, timeout=20)
    results = []
    if isinstance(data, dict) and "results" in data:
        for item in data["results"]:
            results.append({
                "title": item.get("name", "Docker Image"),
                "url": f"https://hub.docker.com/r/{item.get('name', '')}",
                "snippet": truncate_text(item.get("short_description", "")),
                "meta": f"⭐ {item.get('star_count', 0)}",
                "image": None,
            })
    return results


def search_huggingface(query, limit=5):
    url = "https://huggingface.co/api/models"
    params = {"search": query, "limit": limit}
    data = http_get(url, params=params, timeout=20)
    results = []
    if isinstance(data, list):
        for item in data[:limit]:
            results.append({
                "title": item.get("id", "HuggingFace Model"),
                "url": f"https://huggingface.co/{item.get('id', '')}",
                "snippet": f"Downloads: {item.get('downloads', 0)} | Likes: {item.get('likes', 0)}",
                "meta": item.get("pipeline_tag", "model"),
                "image": None,
            })
    return results


def search_flickr(query, limit=5):
    url = "https://www.flickr.com/services/feeds/photos_public.gne"
    params = {"tags": query, "format": "json", "nojsoncallback": 1}
    data = http_get(url, params=params, timeout=20)
    results = []
    if isinstance(data, dict) and "items" in data:
        for item in data["items"][:limit]:
            results.append({
                "title": item.get("title", "Flickr Photo"),
                "url": item.get("link", ""),
                "snippet": truncate_text(item.get("description", "")),
                "meta": f"Auteur: {item.get('author', '')}",
                "image": item.get("media", {}).get("m", ""),
            })
    return results


def search_internet_archive(query, limit=5):
    url = "https://archive.org/advancedsearch.php"
    params = {"q": query, "rows": limit, "output": "json", "fl[]": ["identifier", "title", "description", "year"]}
    data = http_get(url, params=params, timeout=20)
    results = []
    if isinstance(data, dict):
        docs = data.get("response", {}).get("docs", [])
        for doc in docs:
            identifier = doc.get("identifier", "")
            results.append({
                "title": doc.get("title", "Internet Archive Item"),
                "url": f"https://archive.org/details/{identifier}",
                "snippet": truncate_text(" ".join(doc.get("description", []) if isinstance(doc.get("description"), list) else [str(doc.get("description", ""))])),
                "meta": f"Année: {doc.get('year', 'N/A')}",
                "image": f"https://archive.org/services/img/{identifier}" if identifier else None,
            })
    return results


def search_openstreetmap(query, limit=5):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json", "limit": limit}
    headers = {"User-Agent": "SearchEngine/1.0"}
    data = http_get(url, params=params, headers=headers, timeout=20)
    results = []
    if isinstance(data, list):
        for item in data:
            results.append({
                "title": item.get("display_name", "OpenStreetMap Place"),
                "url": f"https://www.openstreetmap.org/{item.get('osm_type', '')}={item.get('osm_id', '')}",
                "snippet": f"Type: {item.get('type', '')}",
                "meta": f"lat:{item.get('lat', '')}, lon:{item.get('lon', '')}",
                "image": None,
            })
    return results
