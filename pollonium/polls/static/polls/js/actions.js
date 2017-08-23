$(document).ready(function() {
    // amount of rows (get value from hidden input field)
    var rowCount = $("#rowCount").val();

    // add click handlers to buttons already present in document
    $(".remove-input").off().on('click', removeInput);

    $(".add-input").click(function(e) {
        e.preventDefault();

        rowCount++;
        $("#rowCount").val(rowCount);

        // add new row at bottom
        var newDiv = '<div class="input-group group-choices" id="choice-row'+rowCount+'"><input autocomplete="off" class="input form-control" id="choice'+rowCount+'" name="choices-choice'+rowCount+'" type="text" placeholder="Option" required/></div>';
        var removeBtnPrev = '<span class="input-group-btn"><button id="remove'+(rowCount-1)+'" class="btn btn-danger remove-input"><span class="glyphicon glyphicon-minus" /></button></span>';

        $("#choice-row"+(rowCount-1)).after(newDiv);
        $("#choice"+rowCount).after($("#btn-plus"));
        $("#choice"+(rowCount-1)).after(removeBtnPrev);

        // set click handler for new added remove button
        $("#remove"+(rowCount-1)).on('click', removeInput);
    });

    function removeInput() {
        // delete the clicked row
        var rid = this.id.charAt(this.id.length-1);
        $(this).parent().parent().remove();

        // update global row counter and rename the next rows
        rowCount--;
        $("#rowCount").val(rowCount);
        renameInputs(rid);
    };

    function renameInputs(startId) {
        // update the row number of all rows from startId to rowCount
        for (let i = parseInt(startId); i <= rowCount; i++) {
            $("#choice"+(i+1)).attr("name", "choices-choice"+i).attr("id", "choice"+i)
            $("#remove"+(i+1)).attr("id", "remove"+i)
            $("#choice-row"+(i+1)).attr("id", "choice-row"+i);
        }
    };
});
