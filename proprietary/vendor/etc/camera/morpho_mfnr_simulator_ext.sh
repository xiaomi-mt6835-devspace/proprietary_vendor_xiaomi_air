SLAKVER="2022.09.19"
PROJECTS=mfnr
BEATH_FLAG=0
INPUT_FLODER=$1
RUN_TIMES=$2
SIMULATOR_PATH="/data/local/tmp/morpho_"$PROJECTS""
SIMULATOR=morpho_"$PROJECTS"_simulator
SIMULATOR_XML=morpho_"$PROJECTS"_params.xml
OUTPUT_PATH=output
LOG_PATH=$SIMULATOR_PATH/$OUTPUT_PATH/runtime.log
ISO_MIN=0
ISO_MAX=99999
ID=-1
ZOOM_RATIO_MIN=0
ZOOM_RATIO_MAX=99
ZOOM_RESULT="0" #"2.15126050"
#HDSR_NUM_MODE=-1
NUM_DROP_FRAME=0
EXTERN_SELECT_BASE=1
FACE_ENABLE=0


echo "SLAKVER=$SLAKVER"

setprop debug.morpho.mfnr.face_enable $FACE_ENABLE

if [ "$1" == "-d" ];then
    INPUT_FLODER=$2
    RUN_TIMES=$3
    BEATH_FLAG=1
    echo "BEATH_FLAG"
fi

function checker_iso() {
	iso=`cat $1 | sed -n "/<params_cfg_iso /p" | sed 's/.*>\(.*\)<.*/\1/g'`
	if (( $iso < $ISO_MIN )) || (( $iso > $ISO_MAX ));then
		return 1
	fi

	return 0
}

function checker_id() {
	id=`cat $1 | sed -n "/<camera_id /p" | sed 's/.*>\(.*\)<.*/\1/g'`
	return $id
}

if [ "$PROJECTS" == "hdsr" ];then
    function checker_zoom_ratio() {
        width=`cat $1 | sed -n "/<width /p" | sed 's/.*>\(.*\)<.*/\1/g'`
        zoom_rect=`cat $1 | sed -n "/<zoom_rect /p" | sed 's/.*>\(.*\)<.*/\1/g'`
        zoom_ratio=`cat $1 | sed -n "/<zoom_ratio /p" | sed 's/.*>\(.*\)<.*/\1/g'`
        tokens_name=(${zoom_rect// / })
        x_begin=${tokens_name[0]}
        x_end=${tokens_name[2]}
        zoom_width=`expr $x_end - $x_begin`
        zoom_test="0"
        ak_zoom=$(echo "$zoom_ratio $zoom_test" | awk '{ if( $1 != $2) print 0;else print 1}')
        if [ $ak_zoom -eq 1 ];
        then
            zoom_ratio=$(echo "$width $zoom_width" | awk '{printf ("%.8f\n",$1/$2)}')
        fi

        min_condition=$(echo "$zoom_ratio $ZOOM_RATIO_MIN" | awk '{ if( $1 >= $2) print 1;else print 0}')
        max_condition=$(echo "$zoom_ratio $ZOOM_RATIO_MAX" | awk '{ if( $1 <= $2) print 1;else print 0}')

        if [ $min_condition -eq 1  -a  $max_condition -eq 1 ];
            then
            echo "***************meta_zoom : $zoom_ratio ************"
            return 0
        fi

        return 1
    }

fi


function simulate_once() {
    inputFloder=$1
    outpuFloder=`basename $inputFloder`
    xmlPath=$inputFloder/$SIMULATOR_XML
    outputFile=`ls $inputFloder | grep -v "xml" | grep -v "txt" |grep -v "yuh" | grep -v "jpg" | grep -v "db" | head -1 | xargs basename`

    if [ -z $outputFile ];then
        echo "   $inputFloder not find image" >> $LOG_PATH
        return -1
    fi

    if [ ! -s "$xmlPath" ];then
        echo "not find $xmlPath"
        return -1
    fi

    checker_iso $xmlPath
    if (($? == 1));then
    	echo "$inputFloder checker_iso faild" >> $LOG_PATH
    	return 0
    fi

    if [ "$PROJECTS" == "hdsr" ];then
        num_mode=`cat $1 | sed -n "/<num_evs /p" | sed 's/.*>\(.*\)<.*/\1/g'`
        checker_zoom_ratio $xmlPath
        if (($? == 1));then
            echo "$inputFloder checker_zoom_ratio faild" >> $LOG_PATH
            return 0
        fi
    fi

    if (($ID != -1));then
        checker_id $xmlPath
        if (($ID != $?));then
            echo "$inputFloder checker_id faild" >> $LOG_PATH
            return 0
        fi
    fi
    

    
    
    if [ "$PROJECTS" == "hdsr" ];then
        set_zoom=0
        ak_set_zoom=$(echo "$ZOOM_RESULT $set_zoom" | awk '{ if( $1 != $2) print 0;else print 1}')
        if [ $ak_set_zoom -eq 1 ];
            then
            if [ $zoom_ratio != 0 ];then
                #set_zoom=$zoom_ratio
                set_zoom=0
            fi
            echo "***************set_zoom : $set_zoom ************"
        else
            set_zoom=$ZOOM_RESULT
            echo "***************set_zoom : $set_zoom ************"
        fi
    fi

    iiid=`cat $xmlPath | sed -n "/<camera_id /p" | sed 's/.*>\(.*\)<.*/\1/g'`
    iiiso=`cat $xmlPath | sed -n "/<params_cfg_iso /p" | sed 's/.*>\(.*\)<.*/\1/g'` 
    echo "***************meta_iso : $iiiso ************"

    if [ "$PROJECTS" == "mfnr" ];then
        bland_num=`cat $xmlPath | sed -n "/<num_evs /p" | sed 's/.*>\(.*\)<.*/\1/g'` 
        bland_test="1"
        ak_bland=$(echo "$bland_num $bland_test" | awk '{ if( $1 == $2) print 0;else print 1}')
        if [ $ak_bland -eq 1 ];
        then
            echo "***************This is HDSR ************"
            tag_sr="HDSR"
        else
            echo "***************This is SR ************"
            tag_sr="SR"
        fi
    fi

    suff=${outputFile##*.}
    prex=${outputFile%%.*}
    prex=`echo ${outputFile}  |sed "s/.yuv//g" |sed "s/morpho_//g" | grep -v "xml" | grep -v "yuh" | head -1 | xargs basename`


    cd     $SIMULATOR_PATH

    if [ ! -d "$OUTPUT_PATH/$outpuFloder" ];then
        mkdir -p $OUTPUT_PATH/$outpuFloder
    fi

    rm -rf $OUTPUT_PATH/$outpuFloder/*
    #setenforce 0
    setprop debug.morpho."$PROJECTS".run_mode 1
    setprop debug.morpho."$PROJECTS".enable 1
    setprop debug.morpho."$PROJECTS".log_level 2
    setprop debug.morpho."$PROJECTS".dump 0
    setprop debug.morpho."$PROJECTS".dump_path $SIMULATOR_PATH/$OUTPUT_PATH/$outpuFloder
    setprop debug.morpho."$PROJECTS".dump_base 0
    export LD_LIBRARY_PATH=./

    echo "    simulate ./$OUTPUT_PATH/$outpuFloder " >> $LOG_PATH
    echo "./$SIMULATOR -o ./$OUTPUT_PATH/$outpuFloder  -x $xmlPath -n $RUN_TIMES  -i $inputFloder/*.${suff}" >> $LOG_PATH
    ./$SIMULATOR -o ./$OUTPUT_PATH/$outpuFloder  -x $xmlPath -n $RUN_TIMES  -z $set_zoom -d $NUM_DROP_FRAME -b $EXTERN_SELECT_BASE -i $inputFloder/*.${suff} >> $LOG_PATH
    time=`date "+%Y%m%d%H%M%S"`
    merge=`ls ./$OUTPUT_PATH/$outpuFloder/*.jpeg | head -n 1 | grep -Eo "merge_[-]?[0-9][0-9]"`
    if [ "$merge" == "" ];then
        merge=`ls ./$OUTPUT_PATH/$outpuFloder/*.jpeg | head -n 1 | grep -Eo "merge_[-]?[0-9]"`
    fi
    face=`ls ./$OUTPUT_PATH/$outpuFloder/*.jpeg | head -n 1 | grep -Eo "face_[-]?[0-9]"`
    mv  ./$OUTPUT_PATH/$outpuFloder/*.jpeg ./$OUTPUT_PATH/$outpuFloder/${prex}_${tag_sr}_"ID"${iiid}_"ISO"${iiiso}_"ZR"${zoom_ratio}_${merge}_${face}_${time}.jpeg
    merge=`ls ./$OUTPUT_PATH/$outpuFloder/*.jpg | head -n 1 | grep -Eo "merge_[-]?[0-9][0-9]"`
    if [ "$merge" == "" ];then
        merge=`ls ./$OUTPUT_PATH/$outpuFloder/*.jpg | head -n 1 | grep -Eo "merge_[-]?[0-9]"`
    fi
    face=`ls ./$OUTPUT_PATH/$outpuFloder/*.jpeg | head -n 1 | grep -Eo "face_[-]?[0-9]"`
    mv  ./$OUTPUT_PATH/$outpuFloder/*.jpg ./$OUTPUT_PATH/$outpuFloder/${prex}_${tag_sr}_"ID"${iiid}_"ISO"${iiiso}_"ZR"${zoom_ratio}_${merge}_${face}_${time}.jpg
    mv  ./$OUTPUT_PATH/$outpuFloder/*.yuv ./$OUTPUT_PATH/$outpuFloder/${prex}.yuv

    echo "    simulate ./$OUTPUT_PATH/$outpuFloder end " >> $LOG_PATH
}

if [ -z $INPUT_FLODER ];then
    echo "please input image dir"
    return -1
fi

if [ -z $RUN_TIMES ];then
    $RUN_TIMES=1
fi

if [ "$BEATH_FLAG"  == "1" ];then
    simulate_once $INPUT_FLODER
    return 0
fi

echo ""  > $LOG_PATH
for floder in `ls -al $INPUT_FLODER | grep "^d" | grep -v '\.' | grep -v '\.\.' | awk '{print $8}'`
do
    echo $INPUT_FLODER/${floder}
    echo $INPUT_FLODER/${floder} >> $LOG_PATH
    simulate_once $INPUT_FLODER/${floder}
    echo "####################################"  >> $LOG_PATH
done
