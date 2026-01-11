# SWBF2 Image Tools (swbf2-image-tools)

A simple desktop utility for converting Star Wars Battlefront II (Frosty Editor) texture exports into Unreal Engine–friendly texture sets. This tool simplifies the repetitive process of unpacking, resizing, and repacking Frosty-exported textures when importing SWBF2 assets into Unreal Engine. Provides a small, focused GUI with configurable options. 

Note: uses Python Imaging Library to perform texture operations.

## How to Use

1. Launch the application
2. Select or drag a folder containing Frosty-exported textures
3. Choose a conversion type (for example: CS/NAM → C/N/ORM)
4. Configure channel mappings and conversion options if needed
5. Select the desired output format
6. Click Process

Texture images are generated in the specified Output folder.

<img width="933" height="724" alt="image" src="https://github.com/user-attachments/assets/2ada284c-4a5a-41ff-b364-33923c1d1fa8" />

## Supported Conversion Types

The application is structured around distinct conversion types. Each conversion defines its own input requirements, processing logic, and output textures.

Additional conversion types may be added in the future.

### CS/NAM → C / N / ORM

This conversion is intended for Frosty Editor exports commonly used by Star Wars Battlefront II assets.

#### Expected Inputs

The tool scans the selected folder for matching texture pairs with the same prefix:

- *_CS textures  
  Color and Smoothness packed into channels

- *_NAM textures  
  Normal, Ambient Occlusion, and Metallic packed into channels

Only prefixes that contain both *_CS and *_NAM textures are considered valid and processed.

#### Outputs

For every valid prefix, the following textures are generated:

- _C  
  Base color texture extracted from the RGB channels of the *_CS texture.

- _N  
  Normal map extracted from the RGB channels of the *_NAM texture.

- _ORM  
  A packed texture containing:
  - R: Ambient Occlusion (from *_NAM)
  - G: Roughness (derived from *_CS smoothness)
  - B: Metallic (from *_NAM)

#### Conversion Behavior

If the *_CS and *_NAM textures differ in resolution, the smoothness channel extracted from *_CS is resized to match the *_NAM resolution before packing. This avoids mismatched channel sizes and ensures proper alignment in the final ORM texture.

Smoothness can optionally be inverted to roughness depending on the target Unreal Engine material workflow.

#### Channel Configuration

All channel mappings for this conversion type are configurable in the UI:

- Smoothness channel selection for *_CS textures
- AO channel selection for *_NAM textures
- Metallic channel selection for *_NAM textures
- Optional inversion of smoothness → roughness
- Optional removal of the alpha channel from the ORM output

These settings allow the conversion to adapt to different export configurations or asset sources.

## Global Output Options

Global output settings apply to all conversion types:

- Output format:
  - PNG
  - TGA
    - Optional RLE compression (lossless, TGA only)

Output files are written using consistent naming based on the detected texture prefix.

## Notes

This tool is intentionally scoped to specific, repeatable texture workflows rather than general-purpose image editing. Its goal is to reduce manual effort, prevent common mistakes, and provide predictable results when working with Frosty-exported assets in Unreal Engine.

Feel free to reach out if you run into any issues or have suggestions to improve the process.
