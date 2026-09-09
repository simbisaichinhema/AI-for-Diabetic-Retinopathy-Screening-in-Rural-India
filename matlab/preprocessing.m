%% Retinal Image Preprocessing in MATLAB
% Preprocesses fundus images for model input.
%
% Requirements:
% - Image Processing Toolbox
% - Computer Vision Toolbox

function processedImg = preprocessing(imgPath, targetSize)
    % Preprocess a retinal fundus image for DR screening.
    %
    % Input:
    %   imgPath - Path to the fundus image
    %   targetSize - [height, width] for resizing (default: [224, 224])
    %
    % Output:
    %   processedImg - Preprocessed image ready for model input

    if nargin < 2
        targetSize = [224, 224];
    end

    % Read image
    img = imread(imgPath);

    % Convert to RGB if needed
    if size(img, 3) == 1
        img = cat(3, img, img, img);
    end

    % Retinal crop (detect circular region)
    gray = rgb2gray(img);
    mask = imbinarize(gray, 'global');
    mask = imfill(mask, 'holes');
    mask = bwareaopen(mask, 1000);

    % Get bounding box of retinal region
    stats = regionprops(mask, 'BoundingBox');
    if ~isempty(stats)
        bbox = stats(1).BoundingBox;
        cropped = imcrop(img, bbox);
    else
        cropped = img;
    end

    % Resize
    resized = imresize(cropped, targetSize);

    % Normalize to [0, 1]
    processedImg = double(resized) / 255.0;

    % ImageNet normalization
    mean = [0.485, 0.456, 0.406];
    std = [0.229, 0.224, 0.225];
    processedImg(:,:,1) = (processedImg(:,:,1) - mean(1)) / std(1);
    processedImg(:,:,2) = (processedImg(:,:,2) - mean(2)) / std(2);
    processedImg(:,:,3) = (processedImg(:,:,3) - mean(3)) / std(3);
end
