def flip_bbox(bboxes):

    # bbox is supposed to be a list or array with values [cls_idx, xmin, ymin, xmax, ymax] * nBoxes

    num_attributes = 5
    num_bboxes = int(len(bboxes) / num_attributes)

    flipped_bboxes = []

    for iBox in range(num_bboxes):
        this_bbox = bboxes[num_attributes*iBox:num_attributes*( 1+iBox )]

        flipped_bboxes.append( this_bbox[0] )

        # horizontal flip
        original_xmin = this_bbox[1]
        original_xmax = this_bbox[3]
        new_xmin = 1 - original_xmax
        new_xmax = 1 - original_xmin

        flipped_bboxes.append(new_xmin)
        flipped_bboxes.append(this_bbox[2])
        flipped_bboxes.append(new_xmax)
        flipped_bboxes.append(this_bbox[4])

    return flipped_bboxes