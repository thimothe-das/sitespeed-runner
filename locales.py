"""
French translations for Sitespeed.io Coach and Lighthouse recommendations.
"""

RECOMMENDATION_TRANSLATIONS = {
    # --- Coach: Performance ---
    "avoidRenderBlocking": {
        "title": "Éliminez les ressources qui bloquent le rendu",
        "description": "Les ressources bloquent le premier rendu de votre page. Chargez le JavaScript de manière asynchrone et mettez en ligne le CSS critique."
    },
    "avoidScalingImages": {
        "title": "Ne redimensionnez pas les images dans le navigateur",
        "description": "Il est préférable de servir des images aux bonnes dimensions plutôt que de laisser le navigateur les redimensionner (ce qui consomme du CPU et de la bande passante)."
    },
    "cssPrint": {
        "title": "Ne chargez pas de feuilles de style spécifiques pour l'impression",
        "description": "Le chargement d'une feuille de style spécifique pour l'impression ralentit la page. Utilisez plutôt une media query @media print dans votre CSS principal."
    },
    "firstContentfulPaint": {
        "title": "Améliorez le First Contentful Paint (FCP)",
        "description": "Le FCP mesure le moment où le premier contenu du DOM est rendu. Un FCP rapide rassure l'utilisateur sur le fait que la page charge."
    },
    "googleTagManager": {
        "title": "Évitez Google Tag Manager si possible",
        "description": "GTM permet d'injecter des scripts qui peuvent dégrader les performances. Utilisez-le avec parcimonie."
    },
    "inlineCss": {
        "title": "Inclinez le CSS critique",
        "description": "Pour un rendu plus rapide, inclinez le CSS nécessaire au contenu au-dessus de la ligne de flottaison et chargez le reste en différé."
    },
    "jquery": {
        "title": "Évitez les versions multiples de jQuery",
        "description": "Le site charge plusieurs versions de jQuery. Nettoyez le code pour n'en utiliser qu'une seule."
    },
    "largestContentfulPaint": {
        "title": "Améliorez le Largest Contentful Paint (LCP)",
        "description": "Le LCP mesure le moment où l'élément le plus large est rendu. Il doit être inférieur à 2,5 secondes."
    },
    "longTasks": {
        "title": "Évitez les longues tâches CPU",
        "description": "Les longues tâches JavaScript bloquent le fil principal et rendent la page non interactive."
    },
    "spof": {
        "title": "Évitez les points de défaillance uniques (SPOF)",
        "description": "Ne chargez pas de scripts tiers de manière synchrone dans le <head>, car s'ils échouent, la page blanche s'affiche."
    },
    "assetsRedirects": {
        "title": "Évitez les redirections d'assets",
        "description": "Chaque redirection ajoute une latence inutile."
    },
    "cacheHeaders": {
        "title": "Configurez les en-têtes de cache",
        "description": "Certains fichiers n'ont pas d'en-tête de cache. Définissez une durée de cache pour éviter les téléchargements répétés."
    },
    "cacheHeadersLong": {
        "title": "Utilisez des durées de cache longues",
        "description": "Pour les fichiers statiques, utilisez une durée de cache d'au moins 30 jours."
    },
    "compressAssets": {
        "title": "Compressez les ressources texte",
        "description": "Activez Gzip ou Brotli pour réduire la taille des fichiers HTML, CSS et JS."
    },
    "connectionKeepAlive": {
        "title": "Utilisez Connection Keep-Alive",
        "description": "Ne fermez pas la connexion après chaque requête. Réutilisez-la."
    },
    "cpuTimeSpentInRendering": {
        "title": "Réduisez le temps CPU de rendu",
        "description": "Le navigateur passe trop de temps à calculer le style et la mise en page."
    },
    "cpuTimeSpentInScripting": {
        "title": "Réduisez le temps d'exécution JavaScript",
        "description": "L'exécution du JavaScript prend trop de temps et ralentit la page."
    },
    "cssSize": {
        "title": "Réduisez la taille du CSS",
        "description": "Le fichier CSS est trop volumineux. Supprimez le CSS inutilisé."
    },
    "documentRedirect": {
        "title": "Évitez les redirections du document principal",
        "description": "La page principale ne devrait pas rediriger, sauf pour passer de HTTP à HTTPS."
    },
    "favicon": {
        "title": "Optimisez le favicon",
        "description": "Le favicon doit être petit et mis en cache."
    },
    "fewFonts": {
        "title": "Limitez le nombre de polices",
        "description": "Trop de polices ralentissent le rendu et peuvent causer des clignotements de texte."
    },
    "fewRequestsPerDomain": {
        "title": "Limitez les requêtes par domaine (HTTP/1)",
        "description": "Si vous utilisez HTTP/1, évitez trop de requêtes simultanées sur le même domaine."
    },
    "headerSize": {
        "title": "Réduisez la taille des en-têtes",
        "description": "Les cookies et autres en-têtes ne doivent pas être trop volumineux."
    },
    "imageSize": {
        "title": "Réduisez la taille des images",
        "description": "Les images sont trop lourdes. Utilisez des formats modernes (WebP, AVIF) et compressez-les."
    },
    "javascriptSize": {
        "title": "Réduisez la taille du JavaScript",
        "description": "Le JavaScript total est trop lourd. Utilisez le code splitting et supprimez le code mort."
    },
    "mimeTypes": {
        "title": "Utilisez les bons types MIME",
        "description": "Configurez correctement les Content-Type pour chaque fichier."
    },
    "optimalCssSize": {
        "title": "Optimisez la taille des paquets CSS",
        "description": "Essayez de garder les fichiers CSS petits (moins de 14.5kB) pour qu'ils tiennent dans la fenêtre TCP initiale."
    },
    "pageSize": {
        "title": "Réduisez le poids total de la page",
        "description": "La page est trop lourde à télécharger pour un réseau mobile."
    },
    "privateAssets": {
        "title": "Attention aux en-têtes privés",
        "description": "Ne marquez pas les assets statiques comme 'private' s'ils sont les mêmes pour tous les utilisateurs."
    },
    "responseOk": {
        "title": "Évitez les erreurs 404/500",
        "description": "Certaines ressources retournent des erreurs. Corrigez les liens brisés."
    },

    # --- Coach: Best Practices ---
    "amp": {
        "title": "Évitez AMP",
        "description": "AMP est une technologie propriétaire de Google. Préférez des pages web standards optimisées."
    },
    "charset": {
        "title": "Déclarez un jeu de caractères",
        "description": "Définissez <meta charset='utf-8'> tôt dans le document."
    },
    "cumulativeLayoutShift": {
        "title": "Évitez les décalages de mise en page (CLS)",
        "description": "Les éléments ne doivent pas bouger pendant le chargement. Définissez des dimensions pour les images et iframes."
    },
    "doctype": {
        "title": "Déclarez le Doctype",
        "description": "Le document doit commencer par <!DOCTYPE html>."
    },
    "language": {
        "title": "Déclarez la langue de la page",
        "description": "Utilisez l'attribut <html lang='fr'> pour l'accessibilité et le SEO."
    },
    "metaDescription": {
        "title": "Ajoutez une meta description",
        "description": "Une description est essentielle pour le SEO et le taux de clic."
    },
    "optimizely": {
        "title": "Utilisez Optimizely avec précaution",
        "description": "Les outils d'A/B testing synchrones ralentissent le rendu."
    },
    "pageTitle": {
        "title": "Ajoutez un titre de page",
        "description": "La balise <title> est cruciale pour le SEO."
    },
    "spdy": {
        "title": "N'utilisez plus SPDY",
        "description": "Passez à HTTP/2 ou HTTP/3."
    },
    "url": {
        "title": "Utilisez des URLs propres",
        "description": "Évitez les espaces, les caractères spéciaux et les identifiants de session dans les URLs."
    },
    "longHeaders": {
        "title": "Évitez les en-têtes trop longs",
        "description": "Les en-têtes de réponse ne doivent pas être excessivement longs."
    },
    "manyHeaders": {
        "title": "Évitez trop d'en-têtes",
        "description": "N'envoyez pas une quantité excessive d'en-têtes HTTP."
    },
    "thirdParty": {
        "title": "Limitez les requêtes tierces",
        "description": "Le contenu tiers (pubs, trackers) peut ralentir considérablement la page."
    },
    "unnecessaryHeaders": {
        "title": "Supprimez les en-têtes inutiles",
        "description": "Retirez les en-têtes comme 'Server', 'X-Powered-By' ou des en-têtes de cache dupliqués."
    },

    # --- Coach: Privacy ---
    "facebook": {
        "title": "Limitez le tracking Facebook",
        "description": "L'intégration de widgets Facebook permet le pistage de vos utilisateurs."
    },
    "fingerprint": {
        "title": "Évitez le fingerprinting",
        "description": "Respectez la vie privée de vos utilisateurs en évitant les techniques d'empreinte numérique."
    },
    "ga": {
        "title": "Limitez Google Analytics",
        "description": "Google Analytics collecte des données personnelles. Envisagez des alternatives plus respectueuses."
    },
    "https": {
        "title": "Utilisez HTTPS",
        "description": "Servez toujours votre contenu via une connexion sécurisée."
    },
    "surveillance": {
        "title": "Évitez les outils de surveillance",
        "description": "Évitez les services connus pour leur capitalisme de surveillance."
    },
    "youtube": {
        "title": "Utilisez le mode confidentialité pour YouTube",
        "description": "Utilisez youtube-nocookie.com pour intégrer des vidéos sans pistage immédiat."
    },
    "contentSecurityPolicyHeader": {
        "title": "Mettez en place une CSP",
        "description": "Utilisez l'en-tête Content-Security-Policy pour prévenir les attaques XSS."
    },
    "googleReCaptcha": {
        "title": "Évitez Google reCAPTCHA",
        "description": "ReCAPTCHA partage des données utilisateur avec Google. Envisagez des alternatives."
    },
    "mixedContent": {
        "title": "Évitez le contenu mixte",
        "description": "Ne chargez pas de ressources HTTP sur une page HTTPS."
    },
    "referrerPolicyHeader": {
        "title": "Configurez Referrer-Policy",
        "description": "Contrôlez quelles informations sont envoyées dans l'en-tête Referer."
    },
    "strictTransportSecurityHeader": {
        "title": "Activez HSTS",
        "description": "Utilisez HTTP Strict Transport Security pour forcer HTTPS."
    },
    "thirdPartyCookies": {
        "title": "Évitez les cookies tiers",
        "description": "Les cookies tiers sont souvent bloqués et nuisent à la vie privée."
    },
    "thirdPartyPrivacy": {
        "title": "Protégez les données utilisateur",
        "description": "Évitez de partager des données utilisateur avec trop de services tiers."
    },

    # --- Lighthouse: Performance & Others ---
    "is-on-https": {
        "title": "Utilise HTTPS",
        "description": "Tous les sites devraient être protégés par HTTPS, même ceux qui ne gèrent pas de données sensibles."
    },
    "viewport": {
        "title": "Possède une balise meta viewport",
        "description": "Ajoutez une balise <meta name=\"viewport\"> pour optimiser l'affichage sur mobile."
    },
    "first-contentful-paint": {
        "title": "First Contentful Paint (FCP)",
        "description": "Le FCP marque le moment où le premier texte ou image est affiché."
    },
    "largest-contentful-paint": {
        "title": "Largest Contentful Paint (LCP)",
        "description": "Le LCP marque le moment où le plus grand élément visible est affiché."
    },
    "total-blocking-time": {
        "title": "Total Blocking Time",
        "description": "Somme de toutes les périodes où le fil principal est bloqué, empêchant l'interactivité."
    },
    "cumulative-layout-shift": {
        "title": "Cumulative Layout Shift (CLS)",
        "description": "Mesure la stabilité visuelle de la page."
    },
    "speed-index": {
        "title": "Speed Index",
        "description": "Le Speed Index indique la rapidité avec laquelle le contenu visible est rempli."
    },
    "interactive": {
        "title": "Time to Interactive",
        "description": "Le temps nécessaire pour que la page devienne pleinement interactive."
    },
    "max-potential-fid": {
        "title": "Délai maximal potentiel de la première entrée",
        "description": "Le pire délai possible que vos utilisateurs pourraient subir."
    },
    "server-response-time": {
        "title": "Réduisez le temps de réponse du serveur",
        "description": "Le serveur met trop de temps à répondre au document principal."
    },
    "render-blocking-resources": {
        "title": "Éliminez les ressources bloquant le rendu",
        "description": "Des ressources bloquent la première peinture de votre page."
    },
    "unused-css-rules": {
        "title": "Réduisez le CSS inutilisé",
        "description": "Supprimez les règles CSS mortes pour réduire la taille des fichiers."
    },
    "unused-javascript": {
        "title": "Réduisez le JavaScript inutilisé",
        "description": "Supprimez le code JS non utilisé pour accélérer le chargement."
    },
    "modern-image-formats": {
        "title": "Servez des images aux formats modernes",
        "description": "Utilisez WebP ou AVIF pour une meilleure compression que PNG ou JPEG."
    },
    "uses-responsive-images": {
        "title": "Dimensionnez correctement les images",
        "description": "Servez des images adaptées à la taille de l'écran de l'utilisateur."
    },
    "efficient-animated-content": {
        "title": "Utilisez des formats vidéo pour le contenu animé",
        "description": "Remplacez les GIFs animés par des vidéos MPEG4/WebM pour économiser des données."
    },
    "duplicated-javascript": {
        "title": "Supprimez les modules JavaScript dupliqués",
        "description": "Supprimez les duplications de modules dans vos bundles."
    },
    "legacy-javascript": {
        "title": "Évitez le JavaScript obsolète",
        "description": "Les polyfills pour les anciens navigateurs ne sont pas nécessaires pour la plupart des utilisateurs modernes."
    },
    "dom-size": {
        "title": "Évitez une taille de DOM excessive",
        "description": "Un DOM trop grand ralentit les calculs de style et le rendu."
    },
    "total-byte-weight": {
        "title": "Évitez les charges utiles réseau énormes",
        "description": "Les charges utiles importantes coûtent cher en données aux utilisateurs."
    },
    "offscreen-images": {
        "title": "Différez le chargement des images hors écran",
        "description": "Utilisez le Lazy Loading pour les images qui ne sont pas visibles immédiatement."
    },
    "unminified-css": {
        "title": "Minifiez le CSS",
        "description": "Minifiez vos fichiers CSS pour réduire leur taille."
    },
    "unminified-javascript": {
        "title": "Minifiez le JavaScript",
        "description": "Minifiez vos fichiers JavaScript pour réduire leur taille."
    },
    "uses-optimized-images": {
        "title": "Optimisez les images",
        "description": "Vos images pourraient être compressées davantage sans perte de qualité visible."
    },
    "uses-text-compression": {
        "title": "Activez la compression de texte",
        "description": "Les ressources textuelles doivent être servies avec une compression (gzip, deflate ou brotli)."
    },
    "uses-rel-preconnect": {
        "title": "Préconnectez-vous aux origines requises",
        "description": "Utilisez `preconnect` pour établir des connexions réseau précoces vers des origines importantes."
    },
    "redirects": {
        "title": "Évitez les redirections multiples",
        "description": "Les redirections introduisent des délais supplémentaires avant le chargement de la page."
    },
    "uses-http2": {
        "title": "Utilisez HTTP/2",
        "description": "HTTP/2 offre de meilleures performances que HTTP/1.1."
    },
    "unsized-images": {
        "title": "Les images n'ont pas de dimensions explicites",
        "description": "Définissez une largeur et une hauteur explicites pour réduire les décalages de mise en page (CLS)."
    },
    "target-size": {
        "title": "Cibles tactiles trop petites",
        "description": "Les éléments interactifs (boutons, liens) doivent être assez grands pour être touchés facilement sur mobile."
    },
    "font-display-insight": {
        "title": "Assurez-vous que le texte reste visible pendant le chargement des polices web",
        "description": "Utilisez la fonctionnalité CSS font-display pour que le texte soit visible pour l'utilisateur pendant le chargement des polices web."
    },
    "forced-reflow-insight": {
        "title": "Évitez les reflows forcés synchrones",
        "description": "Évitez de lire des propriétés de mise en page (comme offsetHeight) immédiatement après les avoir modifiées."
    },
    "image-delivery-insight": {
        "title": "Améliorer la livraison des images",
        "description": "Optimisez la taille et le format des images pour accélérer le chargement."
    },
    "lcp-breakdown-insight": {
        "title": "Décomposition du LCP",
        "description": "Analyse détaillée des composants du temps de chargement du Largest Contentful Paint."
    },
    "lcp-discovery-insight": {
        "title": "Découverte du LCP",
        "description": "Assurez-vous que l'image LCP est découverte tôt par le navigateur."
    },
    "network-dependency-tree-insight": {
        "title": "Arbre de dépendances réseau",
        "description": "Évitez les chaînes de requêtes critiques longues."
    },
    "render-blocking-insight": {
        "title": "Requêtes bloquant le rendu",
        "description": "Identifie les ressources qui empêchent la page de s'afficher rapidement."
    },
    "cache-insight": {
        "title": "Utilisez une mise en cache efficace",
        "description": "Servez les ressources statiques avec une politique de cache efficace."
    },
    "legacy-javascript-insight": {
        "title": "JavaScript hérité",
        "description": "Évitez de servir du code JavaScript transpilé pour d'anciens navigateurs aux navigateurs modernes."
    }
}

