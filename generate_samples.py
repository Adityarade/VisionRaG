import os
from PIL import Image, ImageDraw, ImageFont

def create_sample_images(output_dir="data/sample_images"):
    os.makedirs(output_dir, exist_ok=True)
    
    # Simple helper to get a default font, or fallback to default
    try:
        font_large = ImageFont.truetype("arial.ttf", 40)
        font_medium = ImageFont.truetype("arial.ttf", 24)
        font_small = ImageFont.truetype("arial.ttf", 16)
    except IOError:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Image 1: Office Scene
    img1 = Image.new('RGB', (800, 600), color=(240, 240, 240))
    draw1 = ImageDraw.Draw(img1)
    # Draw a desk (brown rectangle)
    draw1.rectangle([100, 400, 700, 600], fill=(139, 69, 19))
    # Draw a laptop (gray rectangle on desk)
    draw1.rectangle([300, 350, 500, 450], fill=(169, 169, 169))
    draw1.rectangle([320, 360, 480, 430], fill=(0, 0, 0)) # Screen
    # Text on screen
    draw1.text((330, 380), "Monthly Q3 Report", fill=(255, 255, 255), font=font_small)
    # Draw a person (simple shapes)
    draw1.ellipse([350, 200, 450, 300], fill=(255, 220, 177)) # Head
    draw1.rectangle([320, 300, 480, 450], fill=(0, 102, 204)) # Body
    draw1.text((50, 50), "Office Room 101 - Q3 Meeting", fill=(0, 0, 0), font=font_large)
    img1.save(os.path.join(output_dir, "office_scene.png"))

    # Image 2: Street Scene
    img2 = Image.new('RGB', (800, 600), color=(135, 206, 235)) # Sky
    draw2 = ImageDraw.Draw(img2)
    # Draw road
    draw2.rectangle([0, 400, 800, 600], fill=(105, 105, 105))
    # Draw a car
    draw2.rectangle([200, 350, 500, 450], fill=(220, 20, 60))
    draw2.rectangle([250, 300, 400, 350], fill=(200, 20, 60))
    draw2.ellipse([220, 430, 280, 490], fill=(0, 0, 0)) # Wheel 1
    draw2.ellipse([420, 430, 480, 490], fill=(0, 0, 0)) # Wheel 2
    # Street sign
    draw2.rectangle([600, 200, 620, 400], fill=(192, 192, 192)) # Pole
    draw2.rectangle([550, 150, 700, 220], fill=(0, 128, 0)) # Sign
    draw2.text((560, 170), "MAIN ST", fill=(255, 255, 255), font=font_medium)
    draw2.text((50, 50), "Traffic Cam #42 - Downtown", fill=(0, 0, 0), font=font_large)
    img2.save(os.path.join(output_dir, "street_scene.png"))

    # Image 3: Document Page
    img3 = Image.new('RGB', (600, 800), color=(255, 255, 255))
    draw3 = ImageDraw.Draw(img3)
    draw3.text((50, 50), "CONFIDENTIAL INVOICE", fill=(0, 0, 0), font=font_large)
    draw3.text((50, 120), "Invoice Number: INV-2023-001", fill=(0, 0, 0), font=font_medium)
    draw3.text((50, 160), "Date: October 15, 2023", fill=(0, 0, 0), font=font_medium)
    draw3.text((50, 220), "Bill To: Acme Corp", fill=(0, 0, 0), font=font_medium)
    draw3.text((50, 300), "Items:", fill=(0, 0, 0), font=font_medium)
    draw3.text((70, 340), "1. Server Maintenance - $5,000", fill=(0, 0, 0), font=font_medium)
    draw3.text((70, 380), "2. Cloud Storage - $1,200", fill=(0, 0, 0), font=font_medium)
    draw3.text((50, 450), "Total Due: $6,200", fill=(255, 0, 0), font=font_large)
    img3.save(os.path.join(output_dir, "invoice_document.png"))

    # Image 4: Pet Photo
    img4 = Image.new('RGB', (800, 600), color=(144, 238, 144)) # Grass
    draw4 = ImageDraw.Draw(img4)
    # Dog shape
    draw4.rectangle([300, 300, 500, 400], fill=(139, 69, 19)) # Body
    draw4.ellipse([450, 250, 530, 330], fill=(139, 69, 19)) # Head
    draw4.rectangle([320, 400, 340, 480], fill=(139, 69, 19)) # Leg 1
    draw4.rectangle([460, 400, 480, 480], fill=(139, 69, 19)) # Leg 2
    # Text
    draw4.text((50, 50), "Lost Dog Flyer - 'Buddy'", fill=(0, 0, 0), font=font_large)
    draw4.text((50, 100), "Call 555-0199 if found", fill=(0, 0, 0), font=font_medium)
    img4.save(os.path.join(output_dir, "dog_flyer.png"))

    # Image 5: Tech Setup
    img5 = Image.new('RGB', (800, 600), color=(50, 50, 50))
    draw5 = ImageDraw.Draw(img5)
    # Monitor
    draw5.rectangle([200, 150, 600, 400], fill=(20, 20, 20))
    draw5.rectangle([210, 160, 590, 390], fill=(0, 0, 100)) # Screen
    draw5.text((250, 250), "print('Hello World')", fill=(0, 255, 0), font=font_medium)
    # Keyboard
    draw5.rectangle([250, 450, 550, 500], fill=(100, 100, 100))
    # Cell phone
    draw5.rectangle([650, 400, 700, 500], fill=(200, 200, 200))
    draw5.text((660, 420), "12:00", fill=(0, 0, 0), font=font_small)
    draw5.text((50, 50), "Developer Desk Setup", fill=(255, 255, 255), font=font_large)
    img5.save(os.path.join(output_dir, "tech_setup.png"))
    print("Successfully generated 5 sample images.")

if __name__ == "__main__":
    create_sample_images()
