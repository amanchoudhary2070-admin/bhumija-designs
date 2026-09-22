import io
from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from content.models import Banner, Page
from shop.management.commands._placeholder_art import artisan_placeholder, banner_placeholder, product_placeholder
from shop.models import Artisan, Category, Product

# --- Categories: (name, nav_label, icon_key, show_in_nav, children) ------------
CATEGORIES = [
    ("Madhubani Paintings", "", "painting", True, ["Canvas Paintings", "Wall Hangings", "Framed Art"]),
    ("Art & Designs", "", "lotus", True, ["Wall Plates", "Wooden Wall Art", "Motif Prints"]),
    ("Home Decor", "", "home", True, ["Cushion Covers", "Table Decor", "Lamps & Lighting"]),
    ("Interior Design", "", "lamp", True, ["Living Room", "Bedroom", "Dining"]),
    ("Handicrafts", "", "pot", True, ["Terracotta", "Wood Carving", "Paper Mache"]),
    ("Fashion & Textiles", "", "scarf", False, ["Stoles & Dupattas", "Sarees", "Bags"]),
    ("Gifts & Corporate", "Gifts", "gift", True, ["Corporate Gifting", "Festive Gifts", "Personalised"]),
    ("Custom Art", "", "brush", True, []),
]

ARTISANS = [
    ("Kamla Devi", "Jitwarpur, Bihar", "Paints in the Bharni style, filling every figure with dense colour and fine double-line borders. Painting for over twenty years, she trained her daughters in the same tradition."),
    ("Sunita Jha", "Ranti, Bihar", "Known for Kachni (line) work: intricate hatching and cross-hatching instead of flat colour. Her fish and peacock motifs are especially sought after."),
    ("Ramesh Thakur", "Madhubani, Bihar", "A third-generation Godna-style artist, known for tattoo-inspired repeating patterns and nature themes."),
    ("Anita Karn", "Darbhanga, Bihar", "Works across canvas, terracotta and textiles, blending traditional Mithila motifs with contemporary colour palettes for modern homes."),
]

# --- Products: (name, category, price, compare_at, stock, is_featured, details, materials, dimensions, description) --
PRODUCTS = [
    ("Madhubani Radha Krishna Painting", "Canvas Paintings", "4999", "6499", 4, True,
     "Hand-painted on canvas, ready to frame", "Acrylic on canvas, natural pigments", "24 x 36 in",
     "A traditional Radha-Krishna composition rendered in the Bharni style, with dense colour fills and fine double-line borders. Each piece is painted freehand, so brushwork and shading vary slightly from the photo — that variation is part of what makes it handmade."),
    ("Tree of Life Madhubani Painting", "Canvas Paintings", "3999", "", 3, True,
     "A classic Mithila motif symbolising growth", "Acrylic on canvas", "20 x 30 in",
     "The Tree of Life is one of the oldest Madhubani motifs, painted here with birds and flowers nested in its branches. Comes ready to hang."),
    ("Peacock Kachni Wall Hanging", "Wall Hangings", "2799", "3499", 2, False,
     "Fine line (Kachni) work on handmade paper", "Handmade paper, natural pigments, wooden dowel", "18 x 24 in",
     "Two peacocks facing each other, built entirely from fine hatched lines rather than flat colour — a hallmark of the Kachni style. Mounted on a wooden dowel for hanging."),
    ("Framed Fish Motif Painting", "Framed Art", "3299", "", 5, False,
     "Ready to hang, framed in sheesham wood", "Handmade paper, sheesham wood frame", "16 x 20 in",
     "Pairs of fish are a traditional symbol of fertility and good fortune in Mithila art. This piece comes pre-framed in solid sheesham wood."),
    ("Sun and Moon Madhubani Art", "Canvas Paintings", "5499", "", 1, False,
     "One-of-a-kind statement piece", "Acrylic on canvas", "30 x 40 in",
     "A large-format piece depicting the sun and moon in traditional Mithila iconography. Only one is available at this size."),
    ("Bridal Palanquin Scene", "Framed Art", "6999", "8499", 1, False,
     "A detailed procession scene, museum-style framing", "Handmade paper, teak frame", "24 x 32 in",
     "A detailed depiction of a traditional Mithila wedding procession, densely populated with figures, animals and floral borders."),

    ("Handpainted Decorative Wall Plates (Set of 3)", "Wall Plates", "1899", "2299", 8, True,
     "Ceramic plates, hand-painted motifs", "Ceramic, food-safe paint (decorative use)", "8 in diameter each",
     "A set of three ceramic wall plates, each hand-painted with a different traditional motif. Comes with hanging hooks."),
    ("Wooden Fish Wall Art (Pair)", "Wooden Wall Art", "1599", "", 6, False,
     "Carved mango wood, hand-painted", "Mango wood", "12 x 6 in each",
     "A pair of carved wooden fish, hand-painted with Mithila patterns — a popular housewarming gift."),
    ("Lotus Motif Wall Panel", "Motif Prints", "2199", "2699", 3, False,
     "MDF panel with a printed and hand-touched motif", "MDF, mixed media", "18 x 18 in",
     "A lotus medallion panel that pairs well with the Art & Designs range. Lightweight and easy to hang."),

    ("Madhubani Art Cushion Cover (Set of 2)", "Cushion Covers", "1299", "1599", 12, True,
     "Hand block-printed, cotton canvas", "Cotton canvas, 16 x 16 in (cover only)", "16 x 16 in",
     "Two cushion covers hand block-printed with Mithila motifs in a warm palette. Zip closure; insert not included."),
    ("Mithila Handpainted Terracotta Vase", "Table Decor", "2499", "", 4, True,
     "Hand-thrown terracotta, hand-painted", "Terracotta, natural pigments", "12 in height",
     "A hand-thrown terracotta vase finished with a hand-painted Mithila border. Each piece has small variations from the wheel-throwing process."),
    ("Madhubani Art Pendant Lamp", "Lamps & Lighting", "2999", "3599", 3, True,
     "Hand-painted shade, E27 fitting", "Cotton fabric shade over metal frame", "10 in diameter shade",
     "A pendant lamp with a hand-painted Mithila-motif shade that glows warmly when lit. Standard E27 fitting; bulb not included."),
    ("Elephant Motif Table Runner", "Table Decor", "1499", "", 7, False,
     "Hand block-printed cotton", "Cotton, 72 x 14 in", "72 x 14 in",
     "A table runner printed with a marching elephant motif, a nod to the animals that often appear in Mithila folklore."),
    ("Ceramic Tea-Light Holders (Set of 4)", "Table Decor", "899", "1099", 15, False,
     "Hand-painted ceramic", "Ceramic", "3 in height each",
     "Four small tea-light holders, each hand-painted with a different flower motif."),

    ("Terracotta Wall Mask (Durga)", "Terracotta", "2299", "", 2, False,
     "Wheel-thrown and hand-finished", "Terracotta", "14 in height",
     "A wall-mounted terracotta mask in the likeness of Goddess Durga, a traditional Bihar craft form."),
    ("Carved Wooden Elephant", "Wood Carving", "1799", "2199", 6, False,
     "Hand-carved sheesham wood", "Sheesham wood", "8 in height",
     "A hand-carved wooden elephant, a traditional symbol of wisdom and good fortune, finished with natural oil."),
    ("Paper Mache Decorative Box", "Paper Mache", "999", "", 9, False,
     "Hand-painted paper mache", "Paper mache, lacquer finish", "6 x 4 x 3 in",
     "A lightweight decorative box built from layered paper mache and finished with a hand-painted floral pattern."),
    ("Dhokra Metal Wall Art", "Wood Carving", "3499", "", 3, False,
     "Lost-wax cast metal", "Bell metal (Dhokra casting)", "16 x 10 in",
     "A wall panel made using the ancient Dhokra lost-wax metal casting technique, depicting a village scene."),

    ("Hand-Painted Silk Stole", "Stoles & Dupattas", "1899", "2299", 5, False,
     "Hand-painted pure silk", "Mulberry silk", "84 x 28 in",
     "A silk stole hand-painted with a border of Mithila motifs, finished with hand-rolled edges."),
    ("Madhubani Print Cotton Saree", "Sarees", "3299", "3999", 4, False,
     "Hand block-printed cotton saree", "Cotton, 6.3 m with blouse piece", "6.3 m",
     "A cotton saree featuring an all-over Mithila-inspired block print, with a matching blouse piece."),
    ("Handpainted Canvas Tote Bag", "Bags", "799", "", 10, False,
     "Hand-painted canvas, reinforced handles", "Cotton canvas", "14 x 14 x 4 in",
     "A sturdy canvas tote hand-painted with a folk-art fish motif — as useful for groceries as it is decorative."),

    ("Corporate Gifting Art Hamper", "Corporate Gifting", "2999", "3499", 5, False,
     "Painting, coasters and a card, gift-boxed", "Mixed media, gift box", "Box: 12 x 12 x 4 in",
     "A curated hamper for corporate gifting: a small framed painting, a set of coasters and a handwritten card, presented in a branded gift box. Ask us about bulk and logo customisation."),
    ("Festive Diya Set (Set of 6)", "Festive Gifts", "699", "899", 20, False,
     "Hand-painted terracotta diyas", "Terracotta", "2.5 in diameter each",
     "Six hand-painted terracotta diyas, ready for Diwali gifting or your own home."),
    ("Personalised Name Painting", "Personalised", "1999", "", 6, False,
     "Customised with a name or initials", "Acrylic on canvas board", "12 x 16 in",
     "A Mithila-style painting personalised with a name or initials worked into the border — a popular gift for weddings and new homes. Mention the name you'd like at checkout notes, or use our Custom Art page for more control."),

    ("Custom Portrait in Madhubani Style", None, "4499", "", 3, False,
     "Made to order from your photo", "Acrylic on canvas, natural pigments", "16 x 20 in (other sizes on request)",
     "Send us a photo and we'll reinterpret it in traditional Madhubani style. Use the Custom Art page to share details and get a quote before you order."),
]

PAGES = [
    ("shipping-policy", "Shipping Policy", """
<h2>Processing time</h2>
<p>Most pieces are made or hand-finished to order, so please allow 2-5 working days for us to pack your order before it ships. The exact dispatch time is shown on each product page.</p>
<h2>Delivery time</h2>
<p>Once dispatched, orders typically arrive within 4-8 working days depending on your location. Remote areas may take a little longer.</p>
<h2>Shipping charges</h2>
<p>We charge a flat shipping fee shown at checkout, and orders above the free-shipping threshold ship free. Large or fragile pieces are packed with extra padding at no additional cost.</p>
""".strip()),
    ("returns-refunds", "Return &amp; Refund Policy", """
<h2>Returns</h2>
<p>Because most pieces are handmade or made to order, we accept returns only if an item arrives damaged or significantly different from its description. Please write to us within 48 hours of delivery with photos.</p>
<h2>Refunds</h2>
<p>Approved refunds are issued to your original payment method within 5-7 working days of us receiving the returned item.</p>
<h2>Custom orders</h2>
<p>Custom and personalised pieces cannot be returned unless they arrive damaged or defective.</p>
""".strip()),
    ("terms-conditions", "Terms &amp; Conditions", """
<h2>Using this site</h2>
<p>By placing an order with Bhoomija Designs, you agree to provide accurate delivery details and to these terms. Product photos are representative; because pieces are handmade, small variations in colour and pattern are normal and not a defect.</p>
<h2>Pricing</h2>
<p>Prices are listed in Indian Rupees (₹) and include applicable taxes unless stated otherwise. We reserve the right to correct pricing errors before an order is confirmed as paid.</p>
""".strip()),
    ("privacy-policy", "Privacy Policy", """
<h2>What we collect</h2>
<p>We collect the contact and shipping details you provide at checkout, and your account details if you create one. We do not sell your personal data to third parties.</p>
<h2>Payments</h2>
<p>Payments are processed by Razorpay; we do not store your card, UPI or bank details on our servers.</p>
<h2>Contact</h2>
<p>For any privacy questions, write to us using the details on our Contact page.</p>
""".strip()),
]


def _save_image(field_file, name, pil_image):
    buf = io.BytesIO()
    pil_image.save(buf, format="JPEG", quality=86)
    field_file.save(name, ContentFile(buf.getvalue()), save=False)


class Command(BaseCommand):
    help = "Create demo categories, artisans, products, banners and policy pages for Bhoomija Designs."

    def add_arguments(self, parser):
        parser.add_argument("--no-images", action="store_true", help="Skip generating placeholder images (faster).")

    @transaction.atomic
    def handle(self, *args, **options):
        make_images = not options["no_images"]
        created = {"categories": 0, "artisans": 0, "products": 0, "banners": 0, "pages": 0}

        sub_to_parent = {}
        top_level = {}
        for position, (name, nav_label, icon, show_nav, children) in enumerate(CATEGORIES):
            parent, was_created = Category.objects.get_or_create(
                name=name, defaults={"nav_label": nav_label, "icon_key": icon, "show_in_nav": show_nav, "position": position}
            )
            created["categories"] += was_created
            top_level[name] = parent
            for cpos, child_name in enumerate(children):
                child, was_created = Category.objects.get_or_create(
                    name=child_name, defaults={"parent": parent, "position": cpos, "show_in_nav": False, "show_on_home": False}
                )
                created["categories"] += was_created
                sub_to_parent[child_name] = (parent, child)

        artisans = []
        for name, village, bio in ARTISANS:
            artisan, was_created = Artisan.objects.get_or_create(name=name, defaults={"village": village, "bio": bio})
            created["artisans"] += was_created
            if was_created and make_images:
                _save_image(artisan.photo, f"{artisan.slug}.jpg", artisan_placeholder(name))
                artisan.save()
            artisans.append(artisan)

        for i, (name, sub_name, price, compare_at, stock, featured, details, materials, dims, desc) in enumerate(PRODUCTS):
            if Product.objects.filter(name=name).exists():
                continue
            if sub_name is None:
                cats = [top_level["Custom Art"]]
            else:
                parent, child = sub_to_parent[sub_name]
                cats = [parent, child]
            product = Product.objects.create(
                name=name, description=desc, details=details,
                price=Decimal(price), compare_at_price=Decimal(compare_at) if compare_at else None,
                stock=stock, is_featured=featured, materials=materials, dimensions=dims,
                artisan=artisans[i % len(artisans)],
            )
            product.categories.set(cats)
            if make_images:
                _save_image(product.image, f"{product.slug}.jpg", product_placeholder(name))
                product.save()
            created["products"] += 1

        hero_slides = [
            dict(eyebrow="TRADITION MEETS MODERN LIVING", title="Bring Home\nthe", highlight="Soul of Mithila",
                 text="Authentic Madhubani Art, Home Decor & Interior Designs that tell a story.",
                 button_label="Shop Now", link="/shop/", position=0),
            dict(eyebrow="NEW THIS SEASON", title="Hand-painted\nTerracotta &", highlight="Table Decor",
                 text="Small-batch pieces from artisan families in Bihar, made for everyday tables.",
                 button_label="Explore Home Decor", link="/category/home-decor/", position=1),
            dict(eyebrow="FOR YOUR WALLS", title="Statement\nMadhubani", highlight="Paintings",
                 text="From intimate canvases to large framed pieces for a feature wall.",
                 button_label="Shop Paintings", link="/category/madhubani-paintings/", position=2),
        ]
        for data in hero_slides:
            banner, was_created = Banner.objects.get_or_create(placement=Banner.Placement.HERO, position=data["position"], defaults=data)
            created["banners"] += was_created
            if was_created and make_images:
                _save_image(banner.image, f"hero-{data['position']}.jpg", banner_placeholder(data["title"]))
                banner.save()

        _, c1 = Banner.objects.get_or_create(
            placement=Banner.Placement.PROMO_LEFT, defaults=dict(
                title="Interior Design with a\nMithila Touch",
                text="Transform your spaces with timeless art and elegant designs inspired by Mithila culture.",
                button_label="Explore Interior Design", link="/category/interior-design/",
            ))
        created["banners"] += c1
        _, c2 = Banner.objects.get_or_create(
            placement=Banner.Placement.PROMO_RIGHT, defaults=dict(
                title="Custom Art\nJust for You",
                text="Commission your own Madhubani artwork or personalised home decor.",
                button_label="Request Custom Art", link="/custom-art/",
            ))
        created["banners"] += c2

        for slug, title, body in PAGES:
            _, was_created = Page.objects.get_or_create(slug=slug, defaults={"title": title, "body": body})
            created["pages"] += was_created

        self.stdout.write(self.style.SUCCESS(
            f"Demo data ready: {created['categories']} categories, {created['artisans']} artisans, "
            f"{created['products']} products, {created['banners']} banners, {created['pages']} pages."
        ))
